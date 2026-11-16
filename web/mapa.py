"""Mapa de seleção e marcador da tela de localização."""

from base64 import b64encode
from functools import cache
from pathlib import Path

import folium
from folium.plugins import Geocoder
from folium.template import Template

from web.pontos import normalizar

ATIVOS = Path(__file__).resolve().parents[1] / "assets" / "site-location"


@cache
def imagem(nome: str) -> str:
    dados = b64encode((ATIVOS / f"{nome}.svg").read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{dados}"


class Busca(Geocoder):
    """Busca por nome de lugar; escolher um resultado seleciona o ponto como um clique."""

    _template = Template("""
        {% macro script(this, kwargs) %}
            var opcoes = {{ this.options|tojavascript }};
            opcoes["geocoder"] = L.Control.Geocoder[opcoes["provider"]](opcoes["providerOptions"]);
            L.Control.geocoder(opcoes).on("markgeocode", function(e) {
                var mapa = {{ this._parent.get_name() }};
                mapa.setView(e.geocode.center, opcoes["zoom"] || mapa.getZoom());
                mapa.fire("click", {latlng: e.geocode.center});
            }).addTo({{ this._parent.get_name() }});
        {% endmacro %}
    """)


def mapa_mundi(idioma: str = "pt") -> folium.Map:
    mapa = folium.Map(
        location=(10, 0),
        tiles="OpenStreetMap",
        zoom_start=2,
        min_zoom=2,
        max_bounds=True,
        world_copy_jump=True,
        scroll_wheel_zoom=False,  # não prende a rolagem da página; zoom pelos botões, duplo clique ou pinça
    )
    Busca(
        collapsed=False, position="topright", add_marker=False, zoom=9,
        provider_options={"geocodingQueryParams": {"accept-language": idioma}},
        placeholder={"pt": "Buscar cidade ou lugar", "en": "Search a city or place",
                     "es": "Buscar ciudad o lugar"}.get(idioma, "Buscar"),
        error_message={"pt": "Nada encontrado", "en": "Nothing found",
                      "es": "Nada encontrado"}.get(idioma, ""),
    ).add_to(mapa)
    # tons suaves para combinar com a paleta do site; os dados continuam os do OpenStreetMap
    mapa.get_root().header.add_child(folium.Element(
        "<style>.leaflet-tile-pane{filter:saturate(.45) sepia(.12) brightness(1.04);}"
        ".leaflet-container{background:#deecf3;cursor:crosshair;}</style>"
    ))
    return mapa


def clicar(evento: dict) -> tuple[float, float] | None:
    clique = evento.get("last_clicked")
    if clique is None or not -90 <= clique["lat"] <= 90:
        return None
    return normalizar(clique["lat"], clique["lng"])


def marcador(ponto: tuple[float, float] | None) -> folium.FeatureGroup:
    grupo = folium.FeatureGroup(name="Local selecionado")
    if ponto is not None:
        folium.CircleMarker(
            ponto, radius=7, color="white", weight=2, fill=True,
            fill_color="#1d6b43", fill_opacity=1,
        ).add_to(grupo)
    return grupo
