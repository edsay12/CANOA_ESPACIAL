import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core import balanco, culturas

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "culturas.csv"
LAT = -17.8


def cultura_teste(**kw):
    return {**culturas.carregar(FIXTURE)["Teste"], **kw}


def um_dia(**kw):
    """Cultura de ciclo de 1 dia: Ks do dia 1 = ΣETa/ΣETc."""
    return cultura_teste(dias_ini=1, dias_des=0, dias_mid=0, dias_fim=0, **kw)


def serie(inicio, dias, chuva=0.0, tmax=32.0, tmin=18.0):
    datas = pd.date_range(inicio, periods=dias)
    as_arr = lambda v: np.broadcast_to(np.asarray(v, float), (dias,)).copy()
    return pd.DataFrame({"data": datas, "chuva": as_arr(chuva), "tmax": as_arr(tmax), "tmin": as_arr(tmin)})


def etc_diaria(cultura, s, lat=LAT):
    return [
        balanco.kc_diario(cultura, i + 1) * balanco.et0_hargreaves(r.tmax, r.tmin, balanco.ra_mm(lat, r.data.day_of_year))
        for i, r in enumerate(s.itertuples())
    ]


def test_et0_hargreaves():
    # FAO-56 exemplo 8: 20°S, 3 de setembro (dia 246) -> Ra = 32,2 MJ/m²/dia
    assert balanco.ra_mm(-20, 246) == pytest.approx(32.2 * 0.408, abs=0.05)
    # 0,0023 · 10 · (25 + 17,8) · √10
    assert balanco.et0_hargreaves(30, 20, 10) == pytest.approx(0.0023 * 10 * 42.8 * math.sqrt(10))
    assert balanco.et0_hargreaves(30, 20, 10) == pytest.approx(3.1129, abs=1e-4)


def test_et0_penman_monteith():
    # FAO-56 exemplo 18 (Bruxelas, 6 de julho, 50°48'N, 100 m): ET0 = 3,9 mm/dia.
    # ea = 1,409 kPa; com es = 1,997 kPa isso é UR média de 70,56% (eq. 19).
    ra_mj = balanco.ra_mm(50.8, 187) / 0.408
    assert ra_mj == pytest.approx(41.09, abs=0.1)
    et0 = balanco.et0_penman_monteith(21.5, 12.3, 70.56, 2.078, 100.1, 22.07, ra_mj)
    assert et0 == pytest.approx(3.9, abs=0.1)
    ra = balanco.ra_mm(50.8, 187)
    assert balanco.et0_dia(21.5, 12.3, 70.56, 2.078, 100.1, 22.07, ra) == pytest.approx(et0)
    # falta qualquer um dos 4 dados -> Hargreaves naquele dia
    for i in range(4):
        args = [70.56, 2.078, 100.1, 22.07]
        args[i] = float("nan")
        assert balanco.et0_dia(21.5, 12.3, *args, ra) == pytest.approx(balanco.et0_hargreaves(21.5, 12.3, ra))


def test_simulacao_usa_penman_monteith_quando_ha_dados():
    c = um_dia()
    s = serie("2001-07-06", 1, tmax=21.5, tmin=12.3).assign(umid_rel=70.56, vento=2.078, pressao=100.1, rad=22.07)
    r = balanco.simular_safra(s, c, 1000, date(2001, 7, 6), 50.8)
    assert r["etc"] == pytest.approx(float(c["kc_ini"]) * 3.9, abs=0.05)


def test_kc_por_fase():
    c = cultura_teste()  # fases 20/30/40/20, kc 0,3 / 1,2 / 0,6
    assert balanco.kc_diario(c, 1) == pytest.approx(0.3)
    assert balanco.kc_diario(c, 20) == pytest.approx(0.3)
    assert balanco.kc_diario(c, 35) == pytest.approx(0.75)
    assert balanco.kc_diario(c, 50) == pytest.approx(1.2)
    assert balanco.kc_diario(c, 90) == pytest.approx(1.2)
    assert balanco.kc_diario(c, 100) == pytest.approx(0.9)
    assert balanco.kc_diario(c, 110) == pytest.approx(0.6)


def test_balanco_ks_e_deplecao_inicial():
    s = serie("2000-01-01", 5)
    # TAW = 100 · 0,5 = 50; depleção inicial 25. p = 0,6 -> RAW = 30 ≥ 25 -> Ks = 1
    r = balanco.simular_safra(s, um_dia(raiz_m=0.5, p_deplecao=0.6), 100, date(2000, 1, 1), LAT)
    assert r["eta"] == pytest.approx(r["etc"])
    # p = 0,4 -> RAW = 20 < 25 -> Ks = (50 − 25) / (50 − 20)
    r = balanco.simular_safra(s, um_dia(raiz_m=0.5, p_deplecao=0.4), 100, date(2000, 1, 1), LAT)
    assert r["eta"] / r["etc"] == pytest.approx(25 / 30)
    # 2 dias sem chuva, p = 0,5: dia 1 Dr = 25 = RAW -> Ks = 1; dia 2 Dr = 25 + ETc1 -> Ks = (50 − Dr) / 25
    c = cultura_teste(dias_ini=2, dias_des=0, dias_mid=0, dias_fim=0, raiz_m=0.5, p_deplecao=0.5)
    e1, e2 = etc_diaria(c, s.head(2))
    r = balanco.simular_safra(s, c, 100, date(2000, 1, 1), LAT)
    assert r["eta"] == pytest.approx(e1 + (50 - 25 - e1) / 25 * e2)


def test_perda_fao33_limitada():
    c = cultura_teste()
    s = serie("2000-01-01", 110)
    # chuva diária = ETc: depleção fica em 50% da TAW < RAW -> sem perda
    s_ok = s.assign(chuva=etc_diaria(c, s))
    r = balanco.simular_safra(s_ok, c, 100, date(2000, 1, 1), LAT)
    assert r["perda"] == 0 and not r["quebra"]
    # sem chuva e solo quase sem água: ΣETa ≈ 0 -> perda ≈ Ky
    r = balanco.simular_safra(s, cultura_teste(ky=0.8), 0.001, date(2000, 1, 1), LAT)
    assert r["perda"] == pytest.approx(0.8, abs=1e-3)
    # Ky > 1 é limitado a 1
    r = balanco.simular_safra(s, cultura_teste(ky=1.25), 0.001, date(2000, 1, 1), LAT)
    assert r["perda"] == 1.0 and r["quebra"]
    # caso intermediário segue Ky · (1 − ΣETa/ΣETc)
    s_meio = s.assign(chuva=np.where(np.arange(110) % 5 == 0, 12.0, 0.0))
    r = balanco.simular_safra(s_meio, c, 100, date(2000, 1, 1), LAT)
    assert 0 < r["perda"] < 1
    assert r["perda"] == pytest.approx(1.25 * (1 - r["eta"] / r["etc"]))


def test_quebra_acima_de_20():
    s = serie("2000-01-01", 3)
    # p = 0 -> RAW = 0, depleção inicial 25 de 50 -> Ks = 0,5 -> perda = Ky · 0,5
    r = balanco.simular_safra(s, um_dia(raiz_m=0.5, p_deplecao=0, ky=0.4), 100, date(2000, 1, 1), LAT)
    assert r["perda"] == 0.2 and r["quebra"] is False
    r = balanco.simular_safra(s, um_dia(raiz_m=0.5, p_deplecao=0, ky=0.42), 100, date(2000, 1, 1), LAT)
    assert r["perda"] == pytest.approx(0.21) and r["quebra"] is True


def test_nan_chuva_zero_temp_interpolada():
    c = cultura_teste()
    tmax = np.linspace(28, 34, 110)
    chuva = np.where(np.arange(110) % 7 == 0, 15.0, 0.0)
    ref = serie("2000-01-01", 110, chuva=chuva, tmax=tmax)
    com_nan = ref.copy()
    com_nan.loc[[3, 10, 50], "chuva"] = np.nan
    com_nan.loc[[20, 60], "tmax"] = np.nan
    com_nan.loc[[61], "tmin"] = np.nan
    esperado = ref.copy()
    esperado.loc[[3, 10, 50], "chuva"] = 0.0
    r = balanco.simular_safra(com_nan, c, 100, date(2000, 1, 1), LAT)
    e = balanco.simular_safra(esperado, c, 100, date(2000, 1, 1), LAT)
    assert r == pytest.approx(e)
    assert not math.isnan(r["etc"])


def test_ciclo_cruza_o_ano():
    c = cultura_teste()  # 110 dias
    tmax = np.r_[np.full(31, 30.0), np.full(120, 36.0)]  # dezembro/1999 frio, 2000 quente
    s = serie("1999-12-01", 151, tmax=tmax)
    r = balanco.simular_safra(s, c, 100, date(1999, 12, 15), LAT)
    janela = s[s["data"] >= "1999-12-15"].head(110)
    assert janela["data"].iloc[-1] == pd.Timestamp("2000-04-02")
    assert r["etc"] == pytest.approx(sum(etc_diaria(c, janela)))
