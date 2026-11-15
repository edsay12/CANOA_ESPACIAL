"""Mapa de seleção e marcador da tela de localização."""

from base64 import b64encode
from functools import cache
from pathlib import Path

import folium
from branca.element import MacroElement, Template

from web.pontos import normalizar


ATIVOS = Path(__file__).resolve().parents[1] / "assets" / "site-location"


@cache
def imagem(nome: str) -> str:
    dados = b64encode((ATIVOS / f"{nome}.svg").read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{dados}"


class ArteMapa(MacroElement):
    _template = Template("""
        {% macro script(this, kwargs) %}
        const mapa = {{ this._parent.get_name() }};
        const limites = [[-90, -180], [90, 180]];
        const desktop = {{ this.desktop | tojson }};
        const mobile = {{ this.mobile | tojson }};
        const arte = L.imageOverlay(desktop, limites).addTo(mapa);
        const elemento = mapa.getContainer();
        const enquadrar = () => {
            const largura = elemento.clientWidth;
            if (!largura) return;
            const compacto = largura < 600;
            elemento.style.background = "#deecf3";
            elemento.style.cursor = "crosshair";
            arte.setUrl(compacto ? mobile : desktop);
            mapa.invalidateSize({pan: false});
            const zoom = Math.log2(largura / (2 * mapa.options.crs.scale(0)));
            mapa.setMinZoom(zoom);
            mapa.setView([0, 0], zoom, {animate: false});
        };
        let larguraAnterior;
        new ResizeObserver(() => {
            if (larguraAnterior === elemento.clientWidth) return;
            larguraAnterior = elemento.clientWidth;
            enquadrar();
        }).observe(elemento);
        enquadrar();
        {% endmacro %}
    """)

    def __init__(self):
        super().__init__()
        self.desktop = imagem("world-desktop")
        self.mobile = imagem("world-mobile")


def mapa_mundi() -> folium.Map:
    mapa = folium.Map(
        location=(0, 0),
        crs="EPSG4326",
        tiles=None,
        zoom_start=0,
        zoom_snap=0,
        zoom_control=False,
        scroll_wheel_zoom=False,
        attribution_control=False,
        max_bounds=True,
    )
    ArteMapa().add_to(mapa)
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
