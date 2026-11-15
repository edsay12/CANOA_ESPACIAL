import json
import math

import pytest
import requests

from core import power
from core.erros import ErroFonteDados
from tests.unit.conftest import Resposta, resposta_power


def rede(monkeypatch, resposta):
    chamadas = []

    def get(url, params=None, timeout=None, **kw):
        chamadas.append({"url": url, "params": params, "timeout": timeout})
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    monkeypatch.setattr(requests, "get", get)
    return chamadas


def test_sem_cache_chama_api_e_salva(pasta_cache, monkeypatch):
    dados = resposta_power()
    chamadas = rede(monkeypatch, Resposta(dados))
    power.serie(-17.8, -50.923)
    assert len(chamadas) == 1
    c = chamadas[0]
    assert c["url"] == "https://power.larc.nasa.gov/api/temporal/daily/point"
    assert c["params"]["parameters"] == "PRECTOTCORR,T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,GWETROOT,RH2M,WS2M,PS"
    assert c["params"]["community"] == "AG"
    assert (c["params"]["start"], c["params"]["end"]) == ("19950101", "20251231")
    assert (c["params"]["latitude"], c["params"]["longitude"]) == (-17.8, -50.923)
    assert c["params"]["format"] == "JSON"
    assert c["timeout"] == 120
    arquivo = pasta_cache / "power_-17.80_-50.92.json"
    assert json.loads(arquivo.read_text(encoding="utf-8")) == dados


def test_com_cache_nao_usa_rede(pasta_cache, monkeypatch):
    (pasta_cache / "power_-17.80_-50.92.json").write_text(json.dumps(resposta_power(dias=5)), encoding="utf-8")
    chamadas = rede(monkeypatch, AssertionError("não deveria acessar a rede"))
    df = power.serie(-17.8, -50.92)
    assert chamadas == []
    assert len(df) == 5


def test_colunas_um_dia_por_linha(pasta_cache, monkeypatch):
    rede(monkeypatch, Resposta(resposta_power(dias=4)))
    df = power.serie(1, 2)
    assert list(df.columns) == ["data", "chuva", "tmax", "tmin", "rad", "umid_solo", "umid_rel", "vento", "pressao"]
    assert [d.strftime("%Y-%m-%d") for d in df["data"]] == ["1995-01-01", "1995-01-02", "1995-01-03", "1995-01-04"]
    assert df.iloc[0][["chuva", "tmax", "tmin", "rad", "umid_solo", "umid_rel", "vento", "pressao"]].tolist() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]


def test_cache_antigo_sem_umidade_vento_pressao(pasta_cache, monkeypatch):
    antigo = resposta_power(dias=2)
    for p in ("RH2M", "WS2M", "PS"):
        del antigo["properties"]["parameter"][p]
    (pasta_cache / "power_1.00_2.00.json").write_text(json.dumps(antigo), encoding="utf-8")
    df = power.serie(1, 2)
    assert df[["umid_rel", "vento", "pressao"]].isna().all().all() and df["tmax"].tolist() == [2.0, 2.0]


def test_menos_999_vira_nan(pasta_cache, monkeypatch):
    dados = resposta_power(dias=2, valores={"PRECTOTCORR": {"19950102": -999}, "T2M_MIN": {"19950101": -999.0}})
    rede(monkeypatch, Resposta(dados))
    df = power.serie(1, 2)
    assert math.isnan(df.loc[1, "chuva"]) and math.isnan(df.loc[0, "tmin"])
    assert df.loc[0, "chuva"] == 1.0 and df.loc[1, "tmin"] == 3.0


def test_falha_sem_cache_erro_fonte(pasta_cache, monkeypatch):
    for falha in [requests.Timeout("lento"), requests.ConnectionError("fora"), Resposta({}, status=503)]:
        rede(monkeypatch, falha)
        with pytest.raises(ErroFonteDados, match="NASA POWER"):
            power.serie(1, 2)
        assert list(pasta_cache.iterdir()) == []


def test_cache_invalido_busca_de_novo(pasta_cache, monkeypatch):
    arquivo = pasta_cache / "power_1.00_2.00.json"
    arquivo.write_text('{"properties": corrompido', encoding="utf-8")
    dados = resposta_power(dias=3)
    chamadas = rede(monkeypatch, Resposta(dados))
    df = power.serie(1, 2)
    assert len(chamadas) == 1
    assert len(df) == 3
    assert json.loads(arquivo.read_text(encoding="utf-8")) == dados


def test_ponto_invalido_sem_rede(pasta_cache, monkeypatch):
    chamadas = rede(monkeypatch, AssertionError("não deveria acessar a rede"))
    for lat, lon in [(90.5, 0), (-91, 0), (0, 181), (0, -180.5)]:
        with pytest.raises(ValueError):
            power.serie(lat, lon)
    assert chamadas == []
