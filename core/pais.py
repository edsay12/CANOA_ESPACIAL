"""Camada 2 (global): lat/lon -> país e hemisfério (Natural Earth, offline).

Contrato: de(lat, lon) -> {iso2, nome, hemisferio}
"""

import json
from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape

from core import validacao

GEOJSON = Path(__file__).resolve().parent.parent / "data" / "paises.geojson"


@lru_cache(maxsize=4)
def _paises(path):
    feats = json.loads(Path(path).read_text(encoding="utf-8"))["features"]
    paises = []
    for f in feats:
        p = f["properties"]
        iso2 = next((p[k] for k in ("ISO_A2_EH", "ISO_A2", "iso2") if p.get(k) not in (None, "-99")), None)
        nome = p.get("NAME") or p.get("nome")
        paises.append((shape(f["geometry"]), iso2, nome))
    return paises


def de(lat, lon, path=None):
    validacao.ponto(lat, lon)
    pt = Point(lon, lat)
    iso2 = nome = None
    for geom, i, n in _paises(str(path or GEOJSON)):
        if geom.covers(pt):
            iso2, nome = i, n
            break
    return {"iso2": iso2, "nome": nome, "hemisferio": "S" if lat < 0 else "N"}
