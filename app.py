"""Tela pública de localização e abas do FARMBITS."""

import logging
import os
import re
import threading
from base64 import b64encode
from html import escape
from pathlib import Path
from typing import Any

import folium
import streamlit as st
from streamlit_folium import st_folium

from core.erros import ErroFonteDados, ErroPontoInvalido
from web.apresentacao import (
    aviso_anos_sem_estacao,
    cards_clima,
    cards_planos,
    cards_ranking,
    dados_grafico,
    marcadores,
    mensagem_erro,
    prioridades_vazias,
)
from web.i18n import IDIOMAS, t
from web.localizacao import exibir_contexto
from web.mapa import clicar, imagem, mapa_mundi, marcador
from web.pontos import DEMO
from web.servico import Servico


def _svg_img(corpo: str, cor: str, tamanho: int = 20) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{tamanho}" height="{tamanho}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{cor}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{corpo}</svg>'
    )
    b64 = b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img src="data:image/svg+xml;base64,{b64}" alt="" width="{tamanho}" height="{tamanho}">'


_SVGS = {
    "chuva": _svg_img(
        '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
        "#256385",
        20,
    ),
    "calendario": _svg_img(
        '<rect x="3" y="4" width="18" height="18" rx="2"/>'
        '<line x1="16" y1="2" x2="16" y2="6"/>'
        '<line x1="8" y1="2" x2="8" y2="6"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/>',
        "#1d6b43",
        20,
    ),
    "sol": _svg_img(
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41'
        'M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
        "#b87324",
        20,
    ),
    "calor": _svg_img(
        '<path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/>',
        "#9e331e",
        20,
    ),
    "broto": _svg_img(
        '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/>'
        '<path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 '
        '2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 '
        '1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
        "#1d6b43",
        20,
    ),
    "escudo": _svg_img(
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        "#1d6b43",
        16,
    ),
    "moeda": _svg_img(
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M14.8 9A2 2 0 0 0 13 8h-2a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4h-2a2 2 0 0 1-1.8-1"/>'
        '<path d="M12 6v2m0 8v2"/>',
        "#1d6b43",
        16,
    ),
}


def icone(nome: str) -> str:
    return f'<img src="{imagem(nome)}" alt="" width="24" height="24">'


_BRAND_DIR = Path(__file__).resolve().parent / "assets" / "brand"


def _brand_png_uri(nome: str) -> str:
    dados = b64encode((_BRAND_DIR / f"{nome}.png").read_bytes()).decode("ascii")
    return f"data:image/png;base64,{dados}"


def texto_responsivo(chave: str, idioma: str) -> str:
    desktop = escape(t(chave, idioma))
    mobile = escape(t(f"{chave}_mobile", idioma))
    return (
        f'<span class="so-desktop">{desktop}</span>'
        f'<span class="so-mobile">{mobile}</span>'
    )


def escolher_exemplo(ponto: tuple[float, float]) -> None:
    st.session_state.ponto = ponto
    st.session_state.ultimo_clique = None
    st.session_state.versao_mapa += 1


def ir_para_etapa(indice: int) -> None:
    st.session_state.etapa_ativa = indice
    if indice > 1 and st.session_state.get("ponto") is None:
        st.session_state.ponto = next(iter(DEMO.values()))
        st.session_state.ultimo_clique = None
        st.session_state.versao_mapa = st.session_state.get("versao_mapa", 0) + 1


@st.cache_resource
def _preaquecer_demo() -> None:
    """Calcula os 4 pontos da demo em segundo plano quando o site sobe, uma vez por processo."""
    if "PYTEST_CURRENT_TEST" in os.environ:  # nos testes o motor é falso e não deve tocar a rede
        return

    def rodar() -> None:
        from core import clima, contexto, modelo

        for lat, lon in DEMO.values():
            try:
                contexto.contexto(lat, lon)
                clima.clima_mudou(lat, lon)
                modelo.ranking_safra(lat, lon, "03-01")  # data padrão da aba O que plantar
            except Exception:  # pré-cálculo é só aceleração: falhar aqui não pode derrubar o site
                logging.getLogger(__name__).exception("pré-cálculo de (%s, %s) falhou", lat, lon)

    threading.Thread(target=rodar, name="preaquecer-demo", daemon=True).start()


def _obter_servico() -> Servico:
    if st.session_state.get("servico") is not None:
        return st.session_state["servico"]
    return Servico(memoria=st.session_state.contextos)


def _tem_motor_completo(servico: object) -> bool:
    if st.session_state.get("servico") is not None:
        return True
    motor = getattr(servico, "motor", None)
    return callable(getattr(motor, "clima_mudou", None))


def _pontos_nivel(valor_pct: float, inverter: bool = False) -> str:
    n = max(1, min(5, round(valor_pct / 20)))
    classe = "ponto-alerta" if inverter and n >= 3 else "ponto-ok"
    bolas = "".join(
        f'<span class="ponto-indicador {classe if i < n else ""}"></span>'
        for i in range(5)
    )
    return f'<span class="fileira-pontos">{bolas}</span>'


def _extrair_num(texto: str) -> float | None:
    limpo = texto.replace(".", "").replace(",", ".")
    m = re.search(r"[-+]?\d+(?:\.\d+)?", limpo)
    return float(m.group(0)) if m else None


def _barras_comparacao(antes_txt: str, depois_txt: str) -> tuple[int, int]:
    v1 = _extrair_num(antes_txt)
    v2 = _extrair_num(depois_txt)
    if v1 is None or v2 is None or max(abs(v1), abs(v2)) == 0:
        return 75, 75
    topo = max(abs(v1), abs(v2))
    p1 = max(18, min(100, round((abs(v1) / topo) * 100)))
    p2 = max(18, min(100, round((abs(v2) / topo) * 100)))
    return p1, p2


def _html_card_clima(card: dict[str, str], idx: int) -> str:
    chaves_svg = ("chuva", "calendario", "calendario", "sol", "calor")
    svg = _SVGS[chaves_svg[idx % len(chaves_svg)]]
    dif = escape(card["diferenca"])
    # Chuva menor (-), inicio atrasado (+d), fim adiantado (-d), mais veranicos (+) ou calor (+) = alerta
    eh_alerta = (
        (idx == 0 and dif.startswith("-"))
        or (idx == 1 and dif.startswith("+"))
        or (idx == 2 and dif.startswith("-"))
        or (idx in (3, 4) and dif.startswith("+"))
    )
    classe_pilula = "pilula-alerta" if eh_alerta else "pilula-neutra"
    seta = "↓" if dif.startswith("-") else ("↑" if dif.startswith("+") else "→")
    w_antes, w_depois = _barras_comparacao(card["antes"], card["depois"])
    return (
        '<div class="fb-card-clima">'
        f'<div class="fb-card-topo"><span class="fb-icone-clima">{svg}</span>'
        f'<span class="fb-card-rotulo">{escape(card["titulo"])}</span></div>'
        f'<div class="fb-card-valor">{escape(card["depois"])}</div>'
        '<div class="fb-card-comparacao">'
        '<div class="fb-linha-periodo">'
        '<span>Antes</span>'
        '<div class="fb-trilho-mini">'
        f'<div class="fb-preenchimento-antes" style="width:{w_antes}%"></div>'
        "</div>"
        f'<strong>{escape(card["antes"])}</strong>'
        "</div>"
        '<div class="fb-linha-periodo fb-periodo-atual">'
        '<span>Agora</span>'
        '<div class="fb-trilho-mini">'
        f'<div class="fb-preenchimento-agora" style="width:{w_depois}%"></div>'
        "</div>"
        f'<strong>{escape(card["depois"])}</strong>'
        "</div>"
        "</div>"
        f'<div class="fb-pilula-dif {classe_pilula}">{seta} {dif}</div>'
        "</div>"
    )


def _renderizar_aba_clima(
    servico: Servico, lat: float, lon: float, idioma: str
) -> None:
    try:
        with st.spinner(t("carregando", idioma)):
            res = servico.clima(lat, lon, idioma=idioma)
    except (ErroPontoInvalido, ErroFonteDados, ValueError) as exc:
        st.error(mensagem_erro(exc, idioma))
        return

    resumo = res.get("resumo")
    if resumo:
        st.html(
            '<div class="fb-manchete-clima">'
            f'<span class="fb-manchete-icone">{_SVGS["calendario"]}</span>'
            f'<div><span class="fb-manchete-tag">{escape(t("aba_clima", idioma))}</span>'
            f"<h2>{escape(str(resumo))}</h2></div></div>"
        )
        with st.container(key="resumo-clima-sr"):
            st.subheader(str(resumo))

    cartoes, nota_anual = cards_clima(res, idioma=idioma)
    if cartoes:
        cards_html = "".join(
            _html_card_clima(c, i) for i, c in enumerate(cartoes)
        )
        st.html(f'<div class="fb-grade-clima">{cards_html}</div>')
        with st.container(key="metricas-clima-sr"):
            cols = st.columns(len(cartoes))
            for col, card in zip(cols, cartoes, strict=False):
                with col:
                    st.metric(
                        label=card["titulo"],
                        value=card["depois"],
                        delta=card["diferenca"],
                    )
    if nota_anual:
        st.caption(nota_anual)

    df = dados_grafico(res)
    if not df.empty:
        st.html(
            '<div class="fb-cabecalho-grafico">'
            '<div class="fb-grafico-titulo">'
            f'<span class="fb-icone-agua">{_SVGS["chuva"]}</span>'
            '<div><strong>Quanto choveu em cada ano (1995–2025)</strong>'
            '<p>Cada barra mostra o volume acumulado de chuva (mm) no ano</p></div>'
            "</div>"
            '<div class="fb-legenda-grafico">'
            '<span><i class="cor-antes"></i>Antes · 1995–2009</span>'
            '<span><i class="cor-depois"></i>Agora · 2010–2025</span>'
            "</div></div>"
        )
        st.bar_chart(df, x="ano", y="chuva_mm", color="periodo")

    aviso = aviso_anos_sem_estacao(res, idioma=idioma)
    if aviso:
        st.info(aviso)


def _html_card_ranking(card: dict[str, Any], idx: int) -> str:
    destaque = idx == 1
    classe_card = "fb-card-cultura fb-cultura-destaque" if destaque else "fb-card-cultura"
    selo_pos = (
        f'<span class="fb-selo-topo fb-selo-ouro">#{idx} Recomendada</span>'
        if destaque
        else f'<span class="fb-selo-topo">#{idx} Opção</span>'
    )
    nota = max(0.0, min(100.0, float(card["nota"])))
    solo = float(card["nota_solo"]) if card["nota_solo"] is not None else 0.0
    solo_txt = f"{solo:.0f}/100" if card["nota_solo"] is not None else "—"
    explicacao_html = (
        f'<div class="fb-explicacao-cultura">{escape(card["explicacao"])}</div>'
        if card["explicacao"]
        else ""
    )
    return (
        f'<div class="{classe_card}">'
        '<div class="fb-cultura-cabecalho">'
        f'<div class="fb-cultura-titulo"><span class="fb-icone-cultura">{_SVGS["broto"]}</span>'
        f"{selo_pos}"
        f'<h3>{escape(card["titulo"].capitalize())}</h3></div>'
        '<div class="fb-nota-bloco">'
        '<span class="fb-nota-rotulo">Nota geral</span>'
        f'<strong class="fb-nota-numero">{nota:.0f}<span>/100</span></strong>'
        "</div></div>"
        '<div class="fb-barra-fundo">'
        f'<div class="fb-barra-preenchimento" style="width: {nota:.0f}%"></div>'
        "</div>"
        '<div class="fb-grade-atributos">'
        '<div class="fb-atributo">'
        f'<span class="fb-attr-rotulo">{_SVGS["escudo"]} Risco climático</span>'
        f'<strong>{escape(card["risco_txt"])}</strong>'
        f'<small>{escape(card["anos_quebra"])} safras com perda</small>'
        "</div>"
        '<div class="fb-atributo">'
        f'<span class="fb-attr-rotulo">{_SVGS["broto"]} Saúde do solo</span>'
        f"<strong>Solo: {escape(solo_txt)}</strong>"
        f"{_pontos_nivel(solo)}"
        "</div>"
        '<div class="fb-atributo">'
        f'<span class="fb-attr-rotulo">{_SVGS["moeda"]} Retorno estimado</span>'
        f'<strong>{escape(card["retorno_txt"])}</strong>'
        "<small>Estimativa regional</small>"
        "</div>"
        "</div>"
        f"{explicacao_html}"
        "</div>"
    )


def _renderizar_aba_plantar(
    servico: Servico, lat: float, lon: float, idioma: str
) -> dict[str, float]:
    with st.container(key="controles-plantar"):
        col_data, col_ret, col_seg, col_solo = st.columns(4)
        with col_data:
            data_semeadura = st.text_input(
                t("data_semeadura", idioma),
                value="03-01",
                key="data_semeadura",
            )
        with col_ret:
            p_ret = st.slider(
                t("prio_retorno", idioma),
                min_value=0,
                max_value=100,
                value=40,
                key="prio_retorno",
            )
        with col_seg:
            p_seg = st.slider(
                t("prio_seguranca", idioma),
                min_value=0,
                max_value=100,
                value=40,
                key="prio_seguranca",
            )
        with col_solo:
            p_solo = st.slider(
                t("prio_solo", idioma),
                min_value=0,
                max_value=100,
                value=20,
                key="prio_solo",
            )

    pesos = {
        "retorno": float(p_ret),
        "seguranca": float(p_seg),
        "solo": float(p_solo),
    }

    if prioridades_vazias(p_ret, p_seg, p_solo):
        st.warning(t("prioridades_vazias", idioma))
        return pesos

    try:
        with st.spinner(t("carregando", idioma)):
            res = servico.ranking(
                lat,
                lon,
                data_semeadura=data_semeadura,
                prioridades=pesos,
                idioma=idioma,
            )
    except (ErroPontoInvalido, ErroFonteDados, ValueError) as exc:
        st.error(mensagem_erro(exc, idioma))
        return pesos

    cartoes = cards_ranking(res, idioma=idioma)
    if not cartoes:
        st.info(t("ranking_vazio", idioma))
    else:
        for idx, card in enumerate(cartoes, start=1):
            st.html(_html_card_ranking(card, idx))
            if card["aviso_preliminar"]:
                st.warning(card["aviso_preliminar"])

    ignoradas = res.get("culturas_ignoradas") or []
    if ignoradas:
        lista_ign = ", ".join(str(c) for c in ignoradas)
        st.markdown(f"**{t('culturas_ignoradas', idioma)}:** {lista_ign}")

    return pesos


def _html_card_plano(card: dict[str, Any]) -> str:
    atual = bool(card["atual"])
    classe = "fb-card-plano fb-plano-atual" if atual else "fb-card-plano fb-plano-sugerido"
    selo_cls = "fb-selo-ambar" if atual else "fb-selo-ouro"
    nota_txt = f"{card['nota']:.0f}" if card["nota"] is not None else "—"
    solo_txt = (
        f"{card['nota_solo']:.0f}/100"
        if card["nota_solo"] is not None
        else "—"
    )
    passos = "".join(
        f'<div class="fb-passo-safra"><small>Safra {i}</small>'
        f"<strong>{escape(c.capitalize())}</strong></div>"
        + ('<span class="fb-seta-safra">→</span>' if i < len(card["culturas"]) else "")
        for i, c in enumerate(card["culturas"], start=1)
    )
    explicacao_html = (
        f'<div class="fb-explicacao-cultura">{escape(card["explicacao"])}</div>'
        if card["explicacao"]
        else ""
    )
    return (
        f'<div class="{classe}">'
        '<div class="fb-cultura-cabecalho">'
        f'<span class="fb-selo-topo {selo_cls}">{escape(card["rotulo"])}</span>'
        '<div class="fb-nota-bloco">'
        '<span class="fb-nota-rotulo">Nota do plano</span>'
        f'<strong class="fb-nota-numero">{nota_txt}<span>/100</span></strong>'
        "</div></div>"
        f'<div class="fb-trilha-rotacao">{passos}</div>'
        '<div class="fb-grade-atributos">'
        f'<div class="fb-atributo"><span class="fb-attr-rotulo">{_SVGS["escudo"]} Risco médio</span>'
        f'<strong>{escape(card["risco_txt"])}</strong></div>'
        f'<div class="fb-atributo"><span class="fb-attr-rotulo">{_SVGS["broto"]} Efeito no solo</span>'
        f"<strong>Solo: {escape(solo_txt)}</strong></div>"
        f'<div class="fb-atributo"><span class="fb-attr-rotulo">{_SVGS["moeda"]} Retorno anual</span>'
        f'<strong>{escape(card["retorno_txt"])}</strong></div>'
        "</div>"
        f"{explicacao_html}"
        "</div>"
    )


def _renderizar_aba_planos(
    servico: Servico,
    lat: float,
    lon: float,
    candidatas: list[str],
    pesos: dict[str, float],
    idioma: str,
) -> None:
    opcoes = ["", *candidatas]
    with st.container(key="controles-planos"):
        c1, c2, c3 = st.columns(3)
        with c1:
            s1 = st.selectbox(t("safra_1", idioma), opcoes, key="safra_1")
        with c2:
            s2 = st.selectbox(t("safra_2", idioma), opcoes, key="safra_2")
        with c3:
            s3 = st.selectbox(t("safra_3", idioma), opcoes, key="safra_3")

    if not s1 or not s2 or not s3:
        st.info(t("historico_incompleto", idioma))
        return

    try:
        with st.spinner(t("carregando", idioma)):
            res = servico.planos(
                lat,
                lon,
                historico=[s1, s2, s3],
                prioridades=pesos,
                idioma=idioma,
            )
    except (ErroPontoInvalido, ErroFonteDados, ValueError) as exc:
        st.error(mensagem_erro(exc, idioma))
        return

    cartoes = cards_planos(res, idioma=idioma)
    for card in cartoes:
        seq = " → ".join(card["culturas"])
        nota_txt = (
            f"{card['nota']:.0f}" if card["nota"] is not None else "—"
        )
        st.html(_html_card_plano(card))
        with st.container(key=f"plano-sr-{card['rotulo']}"):
            st.subheader(f"{card['rotulo']}: {seq} — {nota_txt}")
        if card["aviso_preliminar"]:
            st.warning(card["aviso_preliminar"])


def _renderizar_por_que_confiar(
    ctx: dict[str, Any],
    idioma: str,
) -> None:
    with st.expander(t("por_que_confiar", idioma)):
        fontes: list[str] = []
        for f in ctx.get("fontes") or []:
            nome = str(f)
            if nome and nome not in fontes:
                fontes.append(nome)
        if "NASA POWER" not in fontes:
            fontes.append("NASA POWER")
        itens_fmt = [
            "[NASA POWER](https://power.larc.nasa.gov/)"
            if f == "NASA POWER"
            else f
            for f in fontes
        ]
        st.markdown(", ".join(itens_fmt))
        st.caption(t("limites", idioma))


def cabecalho(idioma: str, interativo: bool = False) -> None:
    with st.container(
        key="cabecalho",
        horizontal=True,
        vertical_alignment="center",
        horizontal_alignment="distribute",
    ):
        icon_uri = _brand_png_uri("farmbits-icon")
        wordmark_uri = _brand_png_uri("farmbits-wordmark")
        st.html(
            '<div class="marca">'
            f'<img class="marca-vaso" src="{icon_uri}" alt="" width="40" height="53">'
            '<div class="marca-texto">'
            f'<img class="marca-palavra" src="{wordmark_uri}" alt="FARMBits" height="28">'
            f'<p class="subtitulo">{escape(t("subtitulo_marca", idioma))}</p>'
            "</div></div>",
            width="content",
        )
        st.selectbox(
            t("idioma", idioma),
            list(IDIOMAS),
            key="idioma-site",
            label_visibility="collapsed",
            width=166,
        )

    nomes = ("etapa_local", "aba_clima", "aba_plantar", "aba_planos")
    etapa_atual = int(st.session_state.get("etapa_ativa", 1))
    if interativo:
        with st.container(key="trilha-etapas", horizontal=True):
            for indice, nome in enumerate(nomes, 1):
                st.button(
                    t(nome, idioma),
                    key=f"etapa-{indice}",
                    on_click=ir_para_etapa,
                    args=(indice,),
                    type="primary" if indice == etapa_atual else "secondary",
                    width="stretch",
                )
    else:
        ativo = ' aria-current="step"'
        etapas = "".join(
            f'<li{ativo if indice == 1 else ""}>'
            f"<span>{indice}</span><strong>{escape(t(nome, idioma))}</strong></li>"
            for indice, nome in enumerate(nomes, 1)
        )
        st.html(f'<ol class="etapas">{etapas}</ol>')


def exibir_mapa(idioma: str, servico: Servico | None = None) -> None:
    tem_db = bool(
        servico is not None
        and callable(getattr(servico, "db_disponivel", None))
        and servico.db_disponivel()
    )
    mapa = mapa_mundi()
    if tem_db and servico is not None:
        for m in marcadores(servico.observacoes()):
            folium.Marker(
                location=[m["lat"], m["lon"]],
                popup=folium.Popup(m["popup"], max_width=240),
                icon=folium.Icon(color="green", icon="camera"),
            ).add_to(mapa)

    with st.container(key="mapa-local"):
        evento = st_folium(
            mapa,
            key=f"mapa-{st.session_state.versao_mapa}",
            height=430,
            use_container_width=True,
            returned_objects=["last_clicked"],
            feature_group_to_add=marcador(st.session_state.ponto),
        )
        st.html(
            f'<div class="dica-mapa"><i></i>{icone("hand")}'
            f'{texto_responsivo("dica_mapa", idioma)}</div>'
        )
        if tem_db:
            st.button(t("atualizar_fotos", idioma), key="btn_atualizar_fotos")

    ponto = clicar(evento or {})
    if ponto is not None and ponto != st.session_state.ultimo_clique:
        st.session_state.ultimo_clique = ponto
        if st.session_state.ponto != ponto:
            st.session_state.ponto = ponto
            st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="FARMBits",
        page_icon=str(_BRAND_DIR / "farmbits-favicon.png"),
        layout="wide",
    )
    st.session_state.setdefault("ponto", None)
    st.session_state.setdefault("ultimo_clique", None)
    st.session_state.setdefault("versao_mapa", 0)
    st.session_state.setdefault("contextos", {})
    _preaquecer_demo()
    st.session_state.setdefault("etapa_ativa", 1)

    servico = _obter_servico()
    motor_completo = _tem_motor_completo(servico)
    etapa_ativa = int(st.session_state.get("etapa_ativa", 1))

    css = (
        Path(__file__)
        .with_name("web")
        .joinpath("localizacao.css")
        .read_text(encoding="utf-8")
    )
    icones_css = " ".join(
        f"--{nome}: url('{imagem(nome)}');"
        for nome in ("globe", "chevron", "arrow")
    )
    ocultar_mapa_css = (
        ".st-key-cartao-local > div:not(:has([data-testid='stAlert'])) "
        "{ display: none !important; } "
        ".st-key-cartao-local { margin-bottom: 0 !important; padding: 14px 20px !important; } "
        ".st-key-painel-resultados [data-baseweb='tab-list'] { display: none !important; }"
        if motor_completo and etapa_ativa > 1
        else ""
    )
    st.html(f"<style>{css} :root {{ {icones_css} }} {ocultar_mapa_css}</style>")

    idioma = IDIOMAS[st.session_state.get("idioma-site", "Português")]
    cabecalho(idioma, interativo=motor_completo)

    tem_db = bool(
        callable(getattr(servico, "db_disponivel", None))
        and servico.db_disponivel()
    )

    with st.container(key="cartao-local"):
        st.html(
            f'<div class="pergunta"><span class="pin">{icone("location-pin")}</span>'
            f'<div><h1>{escape(t("titulo_local", idioma))}</h1>'
            f'<p>{texto_responsivo("instrucao_local", idioma)}</p></div></div>'
        )
        exibir_mapa(idioma, servico)
        with st.container(key="escolher-local"):
            st.html(
                f'<div class="exemplos-rotulo">{icone("example-pin")}'
                f'<strong>{escape(t("exemplos_local", idioma))}</strong></div>'
            )
            with st.container(horizontal=True, key="exemplos"):
                for indice, (nome, ponto) in enumerate(DEMO.items()):
                    destaque = st.session_state.ponto == ponto or (
                        st.session_state.ponto is None and indice == 0
                    )
                    st.button(
                        nome,
                        key=f"exemplo-{indice}",
                        on_click=escolher_exemplo,
                        args=(ponto,),
                        type="primary" if destaque else "secondary",
                    )

        ctx = None
        if st.session_state.ponto is not None:
            ctx = exibir_contexto(servico, st.session_state.ponto, idioma)
            if ctx is not None and tem_db:
                lat_p, lon_p = st.session_state.ponto
                bot = os.environ.get("TELEGRAM_BOT_USERNAME", "CanoaCampoBot")
                if st.button(
                    t("alertas_telegram", idioma), key="btn_telegram"
                ):
                    fid = servico.fazenda(lat_p, lon_p)
                    st.session_state["telegram_fazenda_id"] = fid
                fid_atual = st.session_state.get("telegram_fazenda_id")
                if fid_atual is not None:
                    url_tg = f"https://t.me/{bot}?start={fid_atual}"
                    st.markdown(f"[{t('alertas_telegram', idioma)}]({url_tg})")

        for tamanho in ("desktop", "mobile"):
            chave = "ver_clima" if tamanho == "desktop" else "ver_clima_mobile"
            st.button(
                t(chave, idioma),
                key=f"ver-clima-{tamanho}",
                width="stretch",
                type="primary",
                disabled=not motor_completo,
                on_click=ir_para_etapa if motor_completo else None,
                args=(2,) if motor_completo else None,
            )

    if ctx is not None and motor_completo:
        lat, lon = st.session_state.ponto
        candidatas = [str(c) for c in ctx.get("culturas", [])]
        with st.container(key="painel-resultados"):
            if etapa_ativa == 3:
                ordem_abas = [
                    ("plantar", t("aba_plantar", idioma)),
                    ("clima", t("aba_clima", idioma)),
                    ("planos", t("aba_planos", idioma)),
                ]
            elif etapa_ativa == 4:
                ordem_abas = [
                    ("planos", t("aba_planos", idioma)),
                    ("clima", t("aba_clima", idioma)),
                    ("plantar", t("aba_plantar", idioma)),
                ]
            else:
                ordem_abas = [
                    ("clima", t("aba_clima", idioma)),
                    ("plantar", t("aba_plantar", idioma)),
                    ("planos", t("aba_planos", idioma)),
                ]

            abas_ui = st.tabs([rotulo for _, rotulo in ordem_abas])
            mapa_abas = dict(
                zip([id_aba for id_aba, _ in ordem_abas], abas_ui, strict=False)
            )

            with mapa_abas["clima"]:
                _renderizar_aba_clima(servico, lat, lon, idioma)
            with mapa_abas["plantar"]:
                pesos = _renderizar_aba_plantar(servico, lat, lon, idioma)
            with mapa_abas["planos"]:
                _renderizar_aba_planos(
                    servico, lat, lon, candidatas, pesos, idioma
                )
            _renderizar_por_que_confiar(ctx, idioma)

            if etapa_ativa in (1, 2):
                st.button(
                    t("aba_plantar", idioma),
                    key="avancar-plantar",
                    width="stretch",
                    type="primary",
                    on_click=ir_para_etapa,
                    args=(3,),
                )
            elif etapa_ativa == 3:
                st.button(
                    t("aba_planos", idioma),
                    key="avancar-planos",
                    width="stretch",
                    type="primary",
                    on_click=ir_para_etapa,
                    args=(4,),
                )


if __name__ == "__main__":
    main()
