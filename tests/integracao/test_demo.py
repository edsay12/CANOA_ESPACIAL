"""Os 4 pontos da demo com o cache versionado em cache/, sem internet (MOT-36, MOT-50, critério de Rio Verde)."""

import time

import pytest
import requests

from core import modelo

PONTOS = {"Rio Verde": (-17.80, -50.92), "Nakuru": (-0.30, 36.07), "Ludhiana": (30.90, 75.85), "Ames": (42.03, -93.62)}


@pytest.fixture(autouse=True)
def sem_internet(monkeypatch):
    def bloqueado(*a, **k):
        raise requests.ConnectionError("teste de integração roda sem internet")

    monkeypatch.setattr(requests, "get", bloqueado)
    monkeypatch.setattr(requests, "post", bloqueado)


@pytest.mark.parametrize("nome", PONTOS)
def test_ranking_menos_de_5s(nome):
    lat, lon = PONTOS[nome]
    inicio = time.monotonic()
    r = modelo.ranking_safra(lat, lon, "03-15")
    assert time.monotonic() - inicio < 5
    assert r["fontes"] and r["fontes"][0] == "NASA POWER"


@pytest.mark.parametrize("nome", PONTOS)
def test_planos_menos_de_10s(nome):
    lat, lon = PONTOS[nome]
    inicio = time.monotonic()
    r = modelo.planos_rotacao(lat, lon, ["Milho", "Milho", "Milho"])
    assert time.monotonic() - inicio < 10
    assert any(p["atual"] for p in r["itens"]) and r["fontes"]


def test_rio_verde_milho_mais_arriscado_que_sorgo():
    r = modelo.ranking_safra(*PONTOS["Rio Verde"], "02-15")
    risco = {i["cultura"]: i["risco_pct"] for i in r["itens"]}
    assert risco["Milho"] > risco["Sorgo granifero"]
    assert all(i["preliminar"] for i in r["itens"])  # nenhuma cultura validada ainda
