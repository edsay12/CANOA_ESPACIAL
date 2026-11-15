"""Camada 1 (global): série diária do NASA POWER (1995–2025) com cache em disco.

Contrato: serie(lat, lon) -> DataFrame [data, chuva, tmax, tmin, rad, umid_solo, umid_rel, vento, pressao]
"""

import logging
import time

import numpy as np
import pandas as pd
import requests

from core import cache, validacao
from core.erros import ErroFonteDados

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
COLUNAS = {"PRECTOTCORR": "chuva", "T2M_MAX": "tmax", "T2M_MIN": "tmin", "ALLSKY_SFC_SW_DWN": "rad", "GWETROOT": "umid_solo",
           "RH2M": "umid_rel", "WS2M": "vento", "PS": "pressao"}
log = logging.getLogger(__name__)


def _baixar(lat, lon):
    params = {
        "parameters": ",".join(COLUNAS),
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": "19950101",
        "end": "20251231",
        "format": "JSON",
    }
    inicio = time.monotonic()
    try:
        r = requests.get(URL, params=params, timeout=120)
        r.raise_for_status()
        dados = r.json()
        dados["properties"]["parameter"]
        return dados
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        raise ErroFonteDados(f"NASA POWER indisponível para ({lat}, {lon}): {e}") from e
    finally:
        log.info("NASA POWER (%.2f, %.2f) %.2f s", lat, lon, time.monotonic() - inicio)


def serie(lat, lon):
    validacao.ponto(lat, lon)
    path = cache.caminho("power", lat, lon)
    dados = cache.ler(path)
    if dados is None:
        dados = _baixar(lat, lon)
        cache.gravar(path, dados)
    p = dados["properties"]["parameter"]
    # cache antigo sem RH2M/WS2M/PS: coluna vazia, e o balanço usa Hargreaves nesses dias (MOT-22)
    df = pd.DataFrame({nome: p.get(chave, {}) for chave, nome in COLUNAS.items()}).sort_index()
    df = df.replace(-999, np.nan).astype(float)
    df.insert(0, "data", pd.to_datetime(df.index, format="%Y%m%d"))
    return df.reset_index(drop=True)
