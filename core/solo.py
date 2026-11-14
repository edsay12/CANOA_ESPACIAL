"""Camada 1 (global): SoilGrids -> água disponível no solo.

Contrato: agua_disponivel(lat, lon) -> {cad_mm, argila_pct, areia_pct, fonte}
"""

import logging
import time

import requests

from core import cache, validacao

URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
CAMADAS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}
PADRAO = {"cad_mm": 100, "argila_pct": None, "areia_pct": None, "fonte": "padrão"}
MO_PCT = 2.5  # shortcut: matéria orgânica fixa; usar a camada soc do SoilGrids se a precisão do solo importar
log = logging.getLogger(__name__)


def _cad_mm(areia_pct, argila_pct):
    """Água disponível (mm por m de solo) = θ33 − θ1500 de Saxton & Rawls (2006)."""
    s, c, om = areia_pct / 100, argila_pct / 100, MO_PCT
    t1500 = -0.024 * s + 0.487 * c + 0.006 * om + 0.005 * s * om - 0.013 * c * om + 0.068 * s * c + 0.031
    t1500 += 0.14 * t1500 - 0.02
    t33 = -0.251 * s + 0.195 * c + 0.011 * om + 0.006 * s * om - 0.027 * c * om + 0.452 * s * c + 0.299
    t33 += 1.283 * t33**2 - 0.374 * t33 - 0.015
    return round((t33 - t1500) * 1000, 1)


def _media_0_30(camada):
    """Média ponderada pela espessura das camadas 0–30 cm, em %."""
    fator = camada.get("unit_measure", {}).get("d_factor", 10)
    valores = {d["label"]: d["values"]["mean"] for d in camada["depths"]}
    return sum(valores[k] * w for k, w in CAMADAS.items()) / sum(CAMADAS.values()) / fator


def _baixar(lat, lon):
    params = [("lon", lon), ("lat", lat), ("property", "clay"), ("property", "sand"), ("value", "mean")]
    params += [("depth", d) for d in CAMADAS]
    inicio = time.monotonic()
    try:
        r = requests.get(URL, params=params, timeout=120)
        r.raise_for_status()
        camadas = {c["name"]: c for c in r.json()["properties"]["layers"]}
        argila, areia = _media_0_30(camadas["clay"]), _media_0_30(camadas["sand"])
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None  # sem dado (falha, ou mar/cidade com valores nulos): o chamador usa o padrão
    finally:
        log.info("SoilGrids (%.2f, %.2f) %.2f s", lat, lon, time.monotonic() - inicio)
    return {"cad_mm": _cad_mm(areia, argila), "argila_pct": round(argila, 1), "areia_pct": round(areia, 1), "fonte": "SoilGrids"}


def agua_disponivel(lat, lon):
    validacao.ponto(lat, lon)
    path = cache.caminho("solo", lat, lon)
    dados = cache.ler(path)
    if dados is None:
        dados = _baixar(lat, lon)
        if dados is None:
            return dict(PADRAO)
        cache.gravar(path, dados)
    return dados
