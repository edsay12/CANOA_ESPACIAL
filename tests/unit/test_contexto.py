from pathlib import Path

import pandas as pd
import pytest

from core import contexto, culturas, global_ctx, pais, power, solo
from core.adaptadores import brasil
from core.erros import ErroPontoInvalido

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
RIO_VERDE, AMES, OCEANO = (-17.8, -50.92), (42.03, -93.62), (-20.0, -30.0)


def serie(chuva_dia=3.0, tmedia_mes=None):
    """Série 1995–1996 com chuva diária constante e tmédia por mês (padrão 25 °C)."""
    datas = pd.date_range("1995-01-01", "1996-12-31")
    t = datas.month.map(lambda m: (tmedia_mes or {}).get(m, 25.0)).astype(float)
    return pd.DataFrame({"data": datas, "chuva": chuva_dia, "tmax": t + 5, "tmin": t - 5})


@pytest.fixture
def fakes(monkeypatch, tmp_path):
    csv = tmp_path / "culturas.csv"
    csv.write_text("cultura,climas\nMilho,tropical;subtropical\nSorgo granifero,arido;tropical\nTrigo,temperado\n")
    monkeypatch.setattr(culturas, "CSV", csv)
    monkeypatch.setattr(pais, "GEOJSON", FIXTURES / "paises.geojson")
    monkeypatch.setattr(global_ctx, "CSV", FIXTURES / "faostat.csv")
    monkeypatch.setattr(brasil, "CSV", tmp_path / "sem_brasil.csv")
    estado = {"serie": serie(), "solo": {"cad_mm": 120, "argila_pct": 40, "areia_pct": 30, "fonte": "SoilGrids"}}
    monkeypatch.setattr(power, "serie", lambda lat, lon: estado["serie"])
    monkeypatch.setattr(solo, "agua_disponivel", lambda lat, lon: dict(estado["solo"]))
    estado["tmp"] = tmp_path
    return estado


def test_campos(fakes):
    r = contexto.contexto(*RIO_VERDE)
    assert {"pais", "culturas", "fontes", "nivel_precisao"} <= set(r)
    assert r["pais"] == {"iso2": "BR", "nome": "Brazil", "hemisferio": "S"}
    assert isinstance(r["culturas"], list) and isinstance(r["fontes"], list)


def test_nivel_pais(fakes):
    # faostat de fixture: BR tem Milho e Sorgo; só Milho existe no culturas.csv
    r = contexto.contexto(*RIO_VERDE)
    assert r["nivel_precisao"] == "pais"
    assert r["culturas"] == ["Milho"]
    assert r["moeda"] == "USD"
    assert r["produtividade"] == {"Milho": {"produtividade_t_ha": 6.0, "preco_t": 180.0}}


def test_nivel_clima(fakes, monkeypatch):
    sem_us = fakes["tmp"] / "faostat.csv"
    sem_us.write_text("iso2,cultura,produtividade_t_ha,preco_usd_t\nBR,Milho,6,180\n")
    monkeypatch.setattr(global_ctx, "CSV", sem_us)
    r = contexto.contexto(*AMES)  # tropical
    assert r["nivel_precisao"] == "clima"
    assert sorted(r["culturas"]) == ["Milho", "Sorgo granifero"]
    fakes["serie"] = serie(tmedia_mes={1: -5.0})  # temperado
    r = contexto.contexto(*AMES)
    assert (r["nivel_precisao"], r["culturas"]) == ("clima", ["Trigo"])


def test_classe_climatica():
    assert contexto.classe_climatica(serie(chuva_dia=1.3)) == "arido"  # ~475 mm/ano
    assert contexto.classe_climatica(serie(chuva_dia=1.5)) == "tropical"  # ~548 mm/ano
    assert contexto.classe_climatica(serie(tmedia_mes={7: 18.0})) == "tropical"
    assert contexto.classe_climatica(serie(tmedia_mes={7: 17.9})) == "subtropical"
    assert contexto.classe_climatica(serie(tmedia_mes={7: 0.0})) == "subtropical"
    assert contexto.classe_climatica(serie(tmedia_mes={1: -0.1})) == "temperado"
    assert contexto.classe_climatica(serie(chuva_dia=1.0, tmedia_mes={1: -10.0})) == "arido"


def test_fontes(fakes):
    assert contexto.contexto(*RIO_VERDE)["fontes"][:2] == ["NASA POWER", "SoilGrids"]
    fakes["solo"] = {"cad_mm": 100, "argila_pct": None, "areia_pct": None, "fonte": "padrão"}
    f = contexto.contexto(*RIO_VERDE)["fontes"]
    assert "NASA POWER" in f and "padrão" in f and "SoilGrids" not in f


def test_fora_de_terra(fakes):
    with pytest.raises(ErroPontoInvalido, match="^ponto fora de terra$"):
        contexto.contexto(*OCEANO)


def test_adaptador_brasil_municipal(fakes, monkeypatch):
    monkeypatch.setattr(brasil, "CSV", FIXTURES / "brasil_municipal.csv")
    r = contexto.contexto(*RIO_VERDE)
    assert r["nivel_precisao"] == "municipal"
    assert r["moeda"] == "BRL"
    assert r["culturas"] == ["Milho"]  # Sorgo do município não existe no culturas.csv de teste
    assert r["produtividade"] == {"Milho": {"produtividade_t_ha": 6.5, "preco_t": 900.0}}
    # fora do Brasil o adaptador não é usado
    assert contexto.contexto(*AMES)["nivel_precisao"] == "pais"
