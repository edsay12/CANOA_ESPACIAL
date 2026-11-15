from datetime import date, timedelta

import pandas as pd
import pytest
import requests

from core import cache, power, recente
from core.erros import ErroFonteDados


def test_ultimos_45_dias_cache_1_dia(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "PASTA", tmp_path)
    chamadas = []

    class Resposta:
        def __init__(self, params):
            self.params = params

        def raise_for_status(self):
            pass

        def json(self):
            inicio = date.fromisoformat(
                self.params["start"][:4]
                + "-"
                + self.params["start"][4:6]
                + "-"
                + self.params["start"][6:]
            )
            fim = date.fromisoformat(
                self.params["end"][:4]
                + "-"
                + self.params["end"][4:6]
                + "-"
                + self.params["end"][6:]
            )
            datas = [
                (inicio + timedelta(days=i)).strftime("%Y%m%d")
                for i in range((fim - inicio).days + 1)
            ]
            parametros = {
                chave: {d: i + 1 for d in datas}
                for i, chave in enumerate(power.COLUNAS)
            }
            parametros["T2M_MIN"][datas[0]] = -999
            parametros["T2M_MAX"][datas[-1]] = -999
            del parametros["PS"]
            return {"properties": {"parameter": parametros}}

    def get(url, params, timeout):
        chamadas.append((url, params.copy(), timeout))
        return Resposta(params)

    monkeypatch.setattr(requests, "get", get)
    hoje = date(2026, 11, 15)
    primeiro = recente.serie(-17.8, -50.923, hoje=hoje)
    assert len(primeiro) == 45
    assert primeiro["data"].iloc[0] == pd.Timestamp("2026-10-02")
    assert primeiro["data"].iloc[-1] == pd.Timestamp("2026-11-15")
    assert list(primeiro.columns) == ["data", *power.COLUNAS.values()]
    assert pd.isna(primeiro.loc[0, "tmin"])
    assert pd.isna(primeiro.loc[44, "tmax"])
    assert primeiro["pressao"].isna().all()
    assert primeiro.loc[0, "chuva"] == 1.0
    assert chamadas[0][0] == power.URL and chamadas[0][2] == 120
    assert chamadas[0][1]["start"] == "20261002" and chamadas[0][1]["end"] == "20261115"
    assert (chamadas[0][1]["latitude"], chamadas[0][1]["longitude"]) == (-17.8, -50.923)
    assert chamadas[0][1]["parameters"] == ",".join(power.COLUNAS)
    assert (tmp_path / "recente_-17.80_-50.92_20261115.json").exists()
    pd.testing.assert_frame_equal(primeiro, recente.serie(-17.8, -50.923, hoje=hoje))
    assert len(chamadas) == 1
    menor = recente.serie(-17.8, -50.923, dias=10, hoje=hoje)
    assert len(menor) == 10
    assert menor["data"].iloc[0] == pd.Timestamp("2026-11-06")
    assert len(chamadas) == 2
    pd.testing.assert_frame_equal(primeiro, recente.serie(-17.8, -50.923, hoje=hoje))
    assert len(chamadas) == 2
    seguinte = recente.serie(-17.8, -50.923, hoje=hoje + timedelta(days=1))
    assert len(chamadas) == 3
    assert seguinte["data"].iloc[0] == pd.Timestamp("2026-10-03")
    assert seguinte["data"].iloc[-1] == pd.Timestamp("2026-11-16")


def test_dados_ausentes_e_entradas_invalidas(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "PASTA", tmp_path)

    class Resposta:
        def raise_for_status(self):
            pass

        def json(self):
            return {"properties": {"parameter": {"PRECTOTCORR": {"20261114": 4}}}}

    chamadas = []
    monkeypatch.setattr(
        requests, "get", lambda *a, **kw: chamadas.append(kw) or Resposta()
    )
    dados = recente.serie(1, 2, hoje=date(2026, 11, 15))
    assert dados["data"].tolist() == [pd.Timestamp("2026-11-14")]
    assert dados.loc[0, "chuva"] == 4
    assert pd.isna(dados.loc[0, "tmax"])
    for lat, lon, dias in [
        (91, 0, 45),
        (0, 181, 45),
        (1, 2, 0),
        (1, 2, -1),
        (1, 2, 1.5),
        (1, 2, True),
    ]:
        with pytest.raises(ValueError):
            recente.serie(lat, lon, dias, hoje=date(2026, 11, 15))
    assert len(chamadas) == 1


def test_falha_fonte_nao_cacheia(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "PASTA", tmp_path)

    def falhar(*args, **kwargs):
        raise requests.Timeout("timeout")

    monkeypatch.setattr(requests, "get", falhar)
    with pytest.raises(ErroFonteDados):
        recente.serie(1, 2, hoje=date(2026, 11, 15))
    assert list(tmp_path.iterdir()) == []
