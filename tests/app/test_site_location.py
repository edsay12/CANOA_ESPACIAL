from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from web import servico
from web.pontos import DEMO


def _app(monkeypatch):
    cliques = {}
    vistos = []
    marcadores = []

    def contexto(lat, lon):
        vistos.append((lat, lon))
        return {"pais": {"nome": "Brasil"}, "nivel_precisao": "municipal"}

    def mapa(*args, feature_group_to_add, **kwargs):
        marcadores.append(feature_group_to_add.get_bounds())
        return cliques

    monkeypatch.setattr(servico, "_motor_padrao", lambda: SimpleNamespace(contexto=contexto))
    monkeypatch.setattr("streamlit_folium.st_folium", mapa)
    return AppTest.from_file(Path(__file__).resolve().parents[2] / "app.py").run(), cliques, vistos, marcadores


def test_each_demo_selects_its_coordinates(monkeypatch):
    tela, _, vistos, marcadores = _app(monkeypatch)
    assert marcadores[-1] == [[None, None], [None, None]]
    for nome, ponto in DEMO.items():
        next(botao for botao in tela.button if botao.label == nome).click().run()
        assert vistos[-1] == ponto
        assert marcadores[-1] == [list(ponto), list(ponto)]
        assert f"{ponto[0]:.2f}, {ponto[1]:.2f}" in tela.success[0].value


def test_language_switch_translates_screen_and_keeps_point(monkeypatch):
    tela, _, _, marcadores = _app(monkeypatch)
    tela.button(key="exemplo-0").click().run()
    for idioma, titulo, clima in (
        ("English", "Where is your land?", "See how my climate has changed"),
        ("Español", "¿Dónde está tu tierra?", "Ver cómo cambió mi clima"),
        ("Português", "Onde fica sua terra?", "Ver o que mudou no meu clima"),
    ):
        tela.selectbox(key="idioma-site").select(idioma).run()
        assert titulo in " ".join(elemento.value for elemento in tela.get("html"))
        assert tela.button(key="ver-clima-desktop").label == clima
        assert marcadores[-1] == [[-17.8, -50.92], [-17.8, -50.92]]


def test_wrapped_map_click_queries_normalized_longitude(monkeypatch):
    tela, cliques, vistos, marcadores = _app(monkeypatch)
    cliques["last_clicked"] = {"lat": -17.804, "lng": 309.076}
    tela.run()
    assert vistos == [(-17.8, -50.92)]
    assert marcadores[-1] == [[-17.8, -50.92], [-17.8, -50.92]]
    assert "-17.80, -50.92" in tela.success[0].value


def test_reselecting_point_reuses_context_in_same_session(monkeypatch):
    tela, _, vistos, _ = _app(monkeypatch)
    tela.button(key="exemplo-0").click().run()
    tela.button(key="exemplo-1").click().run()
    tela.button(key="exemplo-0").click().run()
    assert vistos == [DEMO["Rio Verde (BR)"], DEMO["Nakuru (KE)"]]
    assert "Brasil · -17.80, -50.92 · Dados municipais" == tela.success[0].value


def test_climate_buttons_are_disabled_before_and_after_selection(monkeypatch):
    tela, _, vistos, _ = _app(monkeypatch)
    assert not vistos
    for elemento in ("ver-clima-desktop", "ver-clima-mobile"):
        assert tela.button(key=elemento).disabled
    tela.button(key="exemplo-0").click().run()
    for elemento in ("ver-clima-desktop", "ver-clima-mobile"):
        assert tela.button(key=elemento).disabled
