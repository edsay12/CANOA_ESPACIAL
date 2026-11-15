from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from core.erros import ErroFonteDados, ErroPontoInvalido
from web import servico


def _tela():
    import streamlit as st

    from web.localizacao import exibir_contexto
    from web.servico import Servico

    exibir_contexto(Servico(), st.session_state.ponto, "pt")


def _app(monkeypatch, contexto):
    monkeypatch.setattr(servico, "_motor_padrao", lambda: SimpleNamespace(contexto=contexto))
    tela = AppTest.from_function(_tela)
    tela.session_state.ponto = (-17.8, -50.92)
    return tela.run()


def _brasil():
    return {"pais": {"nome": "Brasil"}, "nivel_precisao": "municipal"}


def test_context_shows_country_coordinates_and_precision(monkeypatch):
    tela = _app(monkeypatch, lambda *_: _brasil())
    assert tela.success[0].value == "Brasil · -17.80, -50.92 · Dados municipais"


def test_off_land_point_displays_error_and_allows_new_location(monkeypatch):
    def contexto(lat, lon):
        if (lat, lon) == (-17.8, -50.92):
            raise ErroPontoInvalido("oceano")
        return _brasil()

    tela = _app(monkeypatch, contexto)
    assert tela.error[0].value == "Esse ponto fica fora de terra firme. Escolha outro lugar."
    tela.session_state.ponto = (-18.0, -50.0)
    tela.run()
    assert not tela.error
    assert tela.success[0].value == "Brasil · -18.00, -50.00 · Dados municipais"


def test_source_failure_displays_error_and_allows_retry(monkeypatch):
    respostas = iter([None, _brasil()])

    def contexto(*_):
        resposta = next(respostas)
        if resposta is None:
            raise ErroFonteDados("offline")
        return resposta

    tela = _app(monkeypatch, contexto)
    assert tela.error[0].value == (
        "Os dados da NASA estão indisponíveis agora. Tente de novo em alguns minutos."
    )
    tela.button[0].click().run()
    assert not tela.error
    assert tela.success[0].value == "Brasil · -17.80, -50.92 · Dados municipais"
