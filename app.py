"""Tela pública de localização do FARMBITS."""

from html import escape
from pathlib import Path

import streamlit as st
from streamlit_folium import st_folium

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


def exibir_mapa(idioma: str) -> None:
    with st.container(key="mapa-local"):
        evento = st_folium(
            mapa_mundi(), key=f'mapa-{st.session_state.versao_mapa}',
            height=430, use_container_width=True, returned_objects=["last_clicked"],
            feature_group_to_add=marcador(st.session_state.ponto),
        )
        st.html(
            f'<div class="dica-mapa"><i></i>{icone("hand")}'
            f'{texto_responsivo("dica_mapa", idioma)}</div>'
        )

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

    with st.container(key="cartao-local"):
        st.html(
            f'<div class="pergunta"><span class="pin">{icone("location-pin")}</span>'
            f'<div><h1>{escape(t("titulo_local", idioma))}</h1>'
            f'<p>{texto_responsivo("instrucao_local", idioma)}</p></div></div>'
        )
        exibir_mapa(idioma)
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

        if st.session_state.ponto is not None:
            servico = Servico(memoria=st.session_state.contextos)
            exibir_contexto(servico, st.session_state.ponto, idioma)

        for tamanho in ("desktop", "mobile"):
            chave = "ver_clima" if tamanho == "desktop" else "ver_clima_mobile"
            st.button(
                t(chave, idioma), key=f"ver-clima-{tamanho}", width="stretch",
                type="primary", disabled=True,
            )


if __name__ == "__main__":
    main()
