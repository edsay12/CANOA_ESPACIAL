"""Estados exibidos ao consultar o contexto de uma localização."""

import streamlit as st

from core.erros import ErroFonteDados, ErroPontoInvalido
from web.i18n import t
from web.servico import Servico


def exibir_contexto(servico: Servico, ponto: tuple[float, float], idioma: str) -> None:
    try:
        with st.spinner(t("carregando", idioma)):
            contexto = servico.contexto(*ponto)
    except ErroPontoInvalido:
        st.error(t("erro_ponto", idioma))
        return
    except ErroFonteDados:
        st.error(t("erro_fonte", idioma))
        st.button(t("tentar_novamente", idioma), key="tentar-contexto")
        return

    nome = contexto["pais"]["nome"]
    precisao = t(f"selo_{contexto['nivel_precisao']}", idioma)
    st.success(f"{nome} · {ponto[0]:.2f}, {ponto[1]:.2f} · {precisao}")
