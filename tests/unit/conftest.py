import pandas as pd
import pytest

from core import cache

PARAMETROS = ["PRECTOTCORR", "T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "GWETROOT"]


@pytest.fixture
def pasta_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "PASTA", tmp_path)
    return tmp_path


def resposta_power(dias=3, valores=None):
    """JSON no formato do NASA POWER daily point para `dias` dias a partir de 1995-01-01."""
    datas = [d.strftime("%Y%m%d") for d in pd.date_range("1995-01-01", periods=dias)]
    valores = valores or {}
    return {
        "properties": {
            "parameter": {
                p: {d: valores.get(p, {}).get(d, float(i + 1)) for d in datas} for i, p in enumerate(PARAMETROS)
            }
        }
    }


class Resposta:
    def __init__(self, dados, status=200):
        self.dados, self.status_code = dados, status

    def json(self):
        return self.dados

    def raise_for_status(self):
        import requests

        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")
