from pathlib import Path

import requests

from core import pais

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "paises.geojson"


def sem_rede(monkeypatch):
    def proibido(*a, **kw):
        raise AssertionError("não deveria acessar a rede")

    monkeypatch.setattr(requests, "get", proibido)
    monkeypatch.setattr(requests, "request", proibido)


def test_pais_e_hemisferio(monkeypatch):
    sem_rede(monkeypatch)
    assert pais.de(-17.8, -50.92, FIXTURE) == {"iso2": "BR", "nome": "Brazil", "hemisferio": "S"}
    assert pais.de(42.03, -93.62, FIXTURE) == {"iso2": "US", "nome": "United States of America", "hemisferio": "N"}
    assert pais.de(0, -50, FIXTURE)["hemisferio"] == "N"


def test_fora_de_pais_iso2_none(monkeypatch):
    sem_rede(monkeypatch)
    r = pais.de(-20.0, -30.0, FIXTURE)
    assert r["iso2"] is None
    assert r["hemisferio"] == "S"
    assert pais.de(10.0, 10.0, FIXTURE)["iso2"] is None
