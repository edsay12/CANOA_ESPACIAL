from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from core.erros import ErroPontoInvalido

RIO_VERDE = (-17.80, -50.92)
NAKURU = (-0.30, 36.07)
DEMONSTRACOES = {
    "Rio Verde (BR)": RIO_VERDE,
    "Nakuru (KE)": NAKURU,
    "Ludhiana (IN)": (30.90, 75.85),
    "Ames (US)": (42.03, -93.62),
}
TEXTOS_ESPERADOS = {
    "Português": (
        "Como o clima do seu lugar mudou e o que plantar agora · dados da NASA",
        "Onde fica sua terra", "Seu clima mudou", "O que plantar", "Planos de rotação",
        "Onde fica sua terra?", "Toque no mapa, no lugar da sua propriedade.",
        "Toque no mapa.", "Toque em qualquer lugar do mapa", "Toque no mapa",
        "Ou escolha um lugar pronto", "Ver o que mudou no meu clima", "Ver meu clima",
        "Idioma", "Dados municipais",
    ),
    "English": (
        "How your local climate has changed and what to plant now · NASA data",
        "Where is your land", "Your climate changed", "What to plant", "Rotation plans",
        "Where is your land?", "Tap your farm’s location on the map.",
        "Tap the map.", "Tap anywhere on the map", "Tap the map",
        "Or choose an example location", "See how my climate has changed",
        "See my climate", "Language", "Municipal data",
    ),
    "Español": (
        "Cómo cambió el clima de tu zona y qué plantar ahora · datos de la NASA",
        "Dónde está tu tierra", "Tu clima cambió", "Qué plantar", "Planes de rotación",
        "¿Dónde está tu tierra?", "Toca en el mapa el lugar de tu propiedad.",
        "Toca el mapa.", "Toca cualquier lugar del mapa", "Toca el mapa",
        "O elige un lugar de ejemplo", "Ver cómo cambió mi clima", "Ver mi clima",
        "Idioma", "Datos municipales",
    ),
}


def _app(monkeypatch, ponto_invalido=None):
    cliques = {}
    vistos = []
    marcadores = []
    mapa_anterior = None

    def contexto(lat, lon):
        vistos.append((lat, lon))
        if (lat, lon) == ponto_invalido:
            raise ErroPontoInvalido("oceano")
        return {"pais": {"nome": "Brasil"}, "nivel_precisao": "municipal"}

    def mapa(*args, key, feature_group_to_add, **kwargs):
        nonlocal mapa_anterior
        if mapa_anterior is not None and key != mapa_anterior:
            cliques.clear()
        mapa_anterior = key
        marcadores.append(feature_group_to_add.get_bounds())
        return cliques

    monkeypatch.setattr("web.servico._motor_padrao", lambda: SimpleNamespace(contexto=contexto))
    monkeypatch.setattr("streamlit_folium.st_folium", mapa)
    return AppTest.from_file(Path(__file__).resolve().parents[2] / "app.py").run(), cliques, vistos, marcadores


def test_each_demo_selects_its_coordinates(monkeypatch):
    tela, _, vistos, marcadores = _app(monkeypatch)
    assert marcadores[-1] == [[None, None], [None, None]]
    botoes = [botao for botao in tela.button if (botao.key or "").startswith("exemplo-")]
    assert [botao.label for botao in botoes] == list(DEMONSTRACOES)
    for nome, ponto in DEMONSTRACOES.items():
        next(botao for botao in tela.button if botao.label == nome).click().run()
        assert vistos[-1] == ponto
        assert marcadores[-1] == [list(ponto), list(ponto)]
        assert f"{ponto[0]:.2f}, {ponto[1]:.2f}" in tela.success[0].value


def test_language_switch_translates_screen_and_keeps_point(monkeypatch):
    tela, _, _, marcadores = _app(monkeypatch)
    assert tela.selectbox(key="idioma-site").value == "Português"
    assert tela.selectbox(key="idioma-site").options == list(TEXTOS_ESPERADOS)
    tela.button(key="exemplo-0").click().run()
    for idioma in ("English", "Español", "Português"):
        traducoes = TEXTOS_ESPERADOS[idioma]
        textos_html, (clima, clima_mobile, rotulo_idioma, selo) = traducoes[:-4], traducoes[-4:]
        tela.selectbox(key="idioma-site").select(idioma).run()
        html = " ".join(elemento.value for elemento in tela.get("html"))
        assert all(f">{texto}<" in html for texto in textos_html)
        assert tela.selectbox(key="idioma-site").label == rotulo_idioma
        assert tela.button(key="ver-clima-desktop").label == clima
        assert tela.button(key="ver-clima-mobile").label == clima_mobile
        assert tela.success[0].value == f"Brasil · -17.80, -50.92 · {selo}"
        assert marcadores[-1] == [list(RIO_VERDE), list(RIO_VERDE)]


def test_wrapped_map_click_queries_normalized_longitude(monkeypatch):
    tela, cliques, vistos, marcadores = _app(monkeypatch)
    cliques["last_clicked"] = {"lat": -17.804, "lng": 309.076}
    tela.run()
    assert vistos == [RIO_VERDE]
    assert marcadores[-1] == [list(RIO_VERDE), list(RIO_VERDE)]
    assert "-17.80, -50.92" in tela.success[0].value


def test_off_land_map_click_allows_demo_selection(monkeypatch):
    tela, cliques, vistos, marcadores = _app(monkeypatch, ponto_invalido=(0, -140))
    cliques["last_clicked"] = {"lat": 0, "lng": -140}
    tela.run()
    assert vistos == [(0, -140)]
    assert tela.error[0].value == "Esse ponto fica fora de terra firme. Escolha outro lugar."
    tela.button(key="exemplo-0").click().run()
    assert not tela.error
    assert vistos[-1] == RIO_VERDE
    assert marcadores[-1] == [list(RIO_VERDE), list(RIO_VERDE)]
    assert tela.success[0].value == "Brasil · -17.80, -50.92 · Dados municipais"


def test_reselecting_point_reuses_context_in_same_session(monkeypatch):
    tela, cliques, vistos, _ = _app(monkeypatch)
    tela.button(key="exemplo-0").click().run()
    tela.button(key="exemplo-1").click().run()
    cliques["last_clicked"] = {"lat": -17.801, "lng": -50.919}
    tela.run()
    assert vistos == [RIO_VERDE, NAKURU]
    assert tela.success[0].value == "Brasil · -17.80, -50.92 · Dados municipais"


def test_climate_buttons_are_disabled_before_and_after_selection(monkeypatch):
    tela, _, vistos, _ = _app(monkeypatch)
    assert not vistos
    for elemento in ("ver-clima-desktop", "ver-clima-mobile"):
        assert tela.button(key=elemento).disabled
    tela.button(key="exemplo-0").click().run()
    for elemento in ("ver-clima-desktop", "ver-clima-mobile"):
        assert tela.button(key=elemento).disabled
