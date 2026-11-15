import json
import logging
import re

import pytest
import requests

from core import power, solo
from tests.unit.conftest import Resposta, resposta_power


def resposta_soilgrids(argila, areia):
    """argila/areia: {label: valor em g/kg} como o SoilGrids v2.0 devolve (d_factor 10)."""

    def camada(nome, valores):
        return {
            "name": nome,
            "unit_measure": {"d_factor": 10, "mapped_units": "g/kg"},
            "depths": [{"label": k, "values": {"mean": v}} for k, v in valores.items()],
        }

    return {"properties": {"layers": [camada("clay", argila), camada("sand", areia)]}}


def rede(monkeypatch, resposta):
    chamadas = []

    def get(url, params=None, timeout=None, **kw):
        chamadas.append({"url": url, "params": params, "timeout": timeout})
        r = resposta(url) if callable(resposta) else resposta
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(requests, "get", get)
    return chamadas


def test_soilgrids_0_30cm_e_cache(pasta_cache, monkeypatch):
    # argila 0-30 cm ponderada: (100*5 + 200*10 + 260*15)/30 = 213.3 g/kg = 21.3 %
    # areia: (500*5 + 400*10 + 400*15)/30 = 416.7 g/kg = 41.7 %
    dados = resposta_soilgrids({"0-5cm": 100, "5-15cm": 200, "15-30cm": 260}, {"0-5cm": 500, "5-15cm": 400, "15-30cm": 400})
    chamadas = rede(monkeypatch, Resposta(dados))
    r = solo.agua_disponivel(-17.8, -50.923)
    assert r["fonte"] == "SoilGrids"
    assert r["argila_pct"] == pytest.approx(21.3, abs=0.05)
    assert r["areia_pct"] == pytest.approx(41.7, abs=0.05)
    # Saxton & Rawls (2006), MO 2,5% (Assumptions da spec): franco com 21,3% argila e 41,7% areia
    assert r["cad_mm"] == pytest.approx(137.6, abs=0.1)
    p = chamadas[0]["params"]
    assert chamadas[0]["url"] == "https://rest.isric.org/soilgrids/v2.0/properties/query"
    assert {v for k, v in p if k == "depth"} == {"0-5cm", "5-15cm", "15-30cm"}
    assert {v for k, v in p if k == "property"} == {"clay", "sand"}
    arquivo = pasta_cache / "solo_-17.80_-50.92.json"
    assert json.loads(arquivo.read_text(encoding="utf-8")) == r

    rede(monkeypatch, AssertionError("não deveria acessar a rede"))
    assert solo.agua_disponivel(-17.8, -50.92) == r

    argiloso = resposta_soilgrids({k: 600 for k in solo.CAMADAS}, {k: 150 for k in solo.CAMADAS})
    arenoso = resposta_soilgrids({k: 50 for k in solo.CAMADAS}, {k: 900 for k in solo.CAMADAS})
    rede(monkeypatch, Resposta(argiloso))
    cad_argiloso = solo.agua_disponivel(1, 1)["cad_mm"]
    rede(monkeypatch, Resposta(arenoso))
    assert solo.agua_disponivel(2, 2)["cad_mm"] < cad_argiloso


def test_falha_usa_padrao(pasta_cache, monkeypatch):
    padrao = {"cad_mm": 100, "argila_pct": None, "areia_pct": None, "fonte": "padrão"}
    nulos = resposta_soilgrids({k: None for k in solo.CAMADAS}, {k: None for k in solo.CAMADAS})
    for falha in [requests.Timeout("lento"), requests.ConnectionError("fora"), Resposta({}, status=500), Resposta(nulos)]:
        chamadas = rede(monkeypatch, falha)
        assert solo.agua_disponivel(-0.3, 36.07) == padrao
        assert chamadas[0]["timeout"] == 10  # demora > 10 s conta como falha
    assert list(pasta_cache.iterdir()) == []


def test_log_requisicoes_power_e_solo(pasta_cache, monkeypatch, caplog):
    soil = resposta_soilgrids({k: 200 for k in solo.CAMADAS}, {k: 400 for k in solo.CAMADAS})
    rede(monkeypatch, lambda url: Resposta(resposta_power() if "power" in url else soil))
    with caplog.at_level(logging.INFO):
        power.serie(-17.8, -50.92)
        solo.agua_disponivel(-17.8, -50.92)
    msgs = [(r.levelno, r.getMessage()) for r in caplog.records]
    for fonte in ["NASA POWER", "SoilGrids"]:
        linhas = [m for lvl, m in msgs if lvl == logging.INFO and fonte in m]
        assert len(linhas) == 1, msgs
        assert "-17.80" in linhas[0] and "-50.92" in linhas[0]
        assert re.search(r"\d+\.\d+ s", linhas[0])
