"""Tela pública de localização e abas do FARMBITS."""

import os
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


def icone(nome: str) -> str:
    return f'<img src="{imagem(nome)}" alt="" width="24" height="24">'


def texto_responsivo(chave: str, idioma: str) -> str:
    desktop = escape(t(chave, idioma))
    mobile = escape(t(f"{chave}_mobile", idioma))
    return f'<span class="so-desktop">{desktop}</span><span class="so-mobile">{mobile}</span>'


def escolher_exemplo(ponto: tuple[float, float]) -> None:
    st.session_state.ponto = ponto
    st.session_state.ultimo_clique = None
    st.session_state.versao_mapa += 1


def _obter_servico() -> Servico:
    if st.session_state.get("servico") is not None:
        return st.session_state["servico"]
    return Servico(memoria=st.session_state.contextos)


def _tem_motor_completo(servico: object) -> bool:
    if st.session_state.get("servico") is not None:
        return True
    motor = getattr(servico, "motor", None)
    return callable(getattr(motor, "clima_mudou", None))


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
        st.subheader(str(resumo))

    cartoes, nota_anual = cards_clima(res, idioma=idioma)
    if cartoes:
        cols = st.columns(len(cartoes))
        for col, card in zip(cols, cartoes, strict=False):
            with col:
                st.metric(
                    label=card["titulo"],
                    value=card["depois"],
                    delta=card["diferenca"],
                )
                st.caption(f"{card['antes']} → {card['depois']}")
    if nota_anual:
        st.caption(nota_anual)

    df = dados_grafico(res)
    if not df.empty:
        st.bar_chart(df, x="ano", y="chuva_mm", color="periodo")

    aviso = aviso_anos_sem_estacao(res, idioma=idioma)
    if aviso:
        st.info(aviso)


def _renderizar_aba_plantar(
    servico: Servico, lat: float, lon: float, idioma: str
) -> dict[str, float]:
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
        for card in cartoes:
            with st.container(border=True):
                st.subheader(f"{card['titulo']} — {card['nota']:.0f}")
                st.markdown(
                    f"**{card['risco_txt']}** · {card['anos_quebra']} · "
                    f"Solo: {card['nota_solo']} · {card['retorno_txt']}"
                )
                if card["explicacao"]:
                    st.caption(card["explicacao"])
                if card["aviso_preliminar"]:
                    st.warning(card["aviso_preliminar"])

    ignoradas = res.get("culturas_ignoradas") or []
    if ignoradas:
        lista_ign = ", ".join(str(c) for c in ignoradas)
        st.markdown(f"**{t('culturas_ignoradas', idioma)}:** {lista_ign}")

    return pesos


def _renderizar_aba_planos(
    servico: Servico,
    lat: float,
    lon: float,
    candidatas: list[str],
    pesos: dict[str, float],
    idioma: str,
) -> None:
    opcoes = ["", *candidatas]
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
        with st.container(border=True):
            seq = " → ".join(card["culturas"])
            nota_txt = (
                f"{card['nota']:.0f}" if card["nota"] is not None else "—"
            )
            st.subheader(f"{card['rotulo']}: {seq} — {nota_txt}")
            st.markdown(
                f"**{card['risco_txt']}** · Solo: {card['nota_solo']} · "
                f"{card['retorno_txt']}"
            )
            if card["explicacao"]:
                st.caption(card["explicacao"])
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






def cabecalho(idioma: str) -> None:
    with st.container(key="cabecalho", horizontal=True, vertical_alignment="center",
                      horizontal_alignment="distribute"):
        st.html(
            f'<div class="marca"><span class="logo">{icone("logo")}</span>'
            '<div><strong>FARMBITS</strong>'
            f'<p class="subtitulo">{escape(t("subtitulo_marca", idioma))}</p></div></div>',
            width="content",
        )
        st.selectbox(
            t("idioma", idioma), list(IDIOMAS), key="idioma-site",
            label_visibility="collapsed", width=166,
        )

    nomes = ("etapa_local", "aba_clima", "aba_plantar", "aba_planos")
    ativo = ' aria-current="step"'
    etapas = "".join(
        f'<li{ativo if indice == 1 else ""}>'
        f'<span>{indice}</span><strong>{escape(t(nome, idioma))}</strong></li>'
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
            mapa, key=f'mapa-{st.session_state.versao_mapa}',
            height=430, use_container_width=True, returned_objects=["last_clicked"],
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
    st.set_page_config(page_title="FARMBITS", page_icon="🌱", layout="wide")
    st.session_state.setdefault("ponto", None)
    st.session_state.setdefault("ultimo_clique", None)
    st.session_state.setdefault("versao_mapa", 0)
    st.session_state.setdefault("contextos", {})

    css = Path(__file__).with_name("web").joinpath("localizacao.css").read_text(encoding="utf-8")
    icones_css = " ".join(f"--{nome}: url('{imagem(nome)}');" for nome in ("globe", "chevron", "arrow"))
    st.html(f"<style>{css} :root {{ {icones_css} }}</style>")

    idioma = IDIOMAS[st.session_state.get("idioma-site", "Português")]
    cabecalho(idioma)

    servico = _obter_servico()
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
                        nome, key=f"exemplo-{indice}", on_click=escolher_exemplo,
                        args=(ponto,), type="primary" if destaque else "secondary",
                    )

        ctx = None
        if st.session_state.ponto is not None:
            ctx = exibir_contexto(servico, st.session_state.ponto, idioma)
            if ctx is not None and tem_db:
                lat_p, lon_p = st.session_state.ponto
                bot = os.environ.get("TELEGRAM_BOT_USERNAME", "CanoaCampoBot")
                if st.button(t("alertas_telegram", idioma), key="btn_telegram"):
                    fid = servico.fazenda(lat_p, lon_p)
                    st.session_state["telegram_fazenda_id"] = fid
                fid_atual = st.session_state.get("telegram_fazenda_id")
                if fid_atual is not None:
                    url_tg = f"https://t.me/{bot}?start={fid_atual}"
                    st.markdown(f"[{t('alertas_telegram', idioma)}]({url_tg})")

        for tamanho in ("desktop", "mobile"):
            chave = "ver_clima" if tamanho == "desktop" else "ver_clima_mobile"
            st.button(
                t(chave, idioma), key=f"ver-clima-{tamanho}", width="stretch",
                type="primary", disabled=True,
            )

    if ctx is not None and _tem_motor_completo(servico):
        lat, lon = st.session_state.ponto
        with st.container(key="painel-resultados"):
            aba_clima, aba_plantar, aba_planos = st.tabs(
                [
                    t("aba_clima", idioma),
                    t("aba_plantar", idioma),
                    t("aba_planos", idioma),
                ]
            )
            with aba_clima:
                _renderizar_aba_clima(servico, lat, lon, idioma)
            with aba_plantar:
                pesos = _renderizar_aba_plantar(servico, lat, lon, idioma)
            with aba_planos:
                candidatas = [str(c) for c in ctx.get("culturas", [])]
                _renderizar_aba_planos(
                    servico, lat, lon, candidatas, pesos, idioma
                )
            _renderizar_por_que_confiar(ctx, idioma)



if __name__ == "__main__":
    main()
