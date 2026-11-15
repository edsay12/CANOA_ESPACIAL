from pathlib import Path

import pandas as pd
import pytest

from core import balanco, clima, culturas, pais, power, solo

DIA = pd.Timedelta(days=1)


def base():
    """1995–2025 sem chuva, tmax 30 °C, tmin 18 °C."""
    return pd.DataFrame({"data": pd.date_range("1995-01-01", "2025-12-31"), "chuva": 0.0, "tmax": 30.0, "tmin": 18.0})


def faixa(df, ini, fim, col, valor):
    df.loc[(df["data"] >= pd.Timestamp(ini)) & (df["data"] <= pd.Timestamp(fim)), col] = valor


def plantar(df, ini, ultimo, secos=(), quentes=()):
    """Estação: 3 dias de 7 mm a partir de `ini`, depois 1 mm/dia até `ultimo` (o fim esperado).

    `secos` e `quentes` são (dias após o início, duração): dias sem chuva e dias com tmax 36 °C.
    Devolve a chuva esperada da estação.
    """
    ini, ultimo = pd.Timestamp(ini), pd.Timestamp(ultimo)
    faixa(df, ini, ini + 2 * DIA, "chuva", 7.0)
    faixa(df, ini + 3 * DIA, ultimo, "chuva", 1.0)
    for o, n in secos:
        faixa(df, ini + o * DIA, ini + (o + n - 1) * DIA, "chuva", 0.0)
    for o, n in quentes:
        faixa(df, ini + o * DIA, ini + (o + n - 1) * DIA, "tmax", 36.0)
    return 21 + (ultimo - ini).days - 2 - sum(n for _, n in secos)


@pytest.fixture
def ponto(monkeypatch):
    estado = {"serie": base(), "hemisferio": "S"}
    monkeypatch.setattr(power, "serie", lambda lat, lon: estado["serie"])
    monkeypatch.setattr(pais, "de", lambda lat, lon: {"iso2": "BR", "nome": "Brazil", "hemisferio": estado["hemisferio"]})
    return estado


def cenario_mudanca(df):
    """1995–2009: 15/out a 31/mar, sem veranicos, 5 dias quentes. 2010–2024: 05/nov a 10/mar, 2 veranicos, 12 dias quentes."""
    esperado = {"A": [], "B": []}
    for ano in range(1995, 2010):
        esperado["A"].append(plantar(df, f"{ano}-10-15", f"{ano + 1}-03-31", quentes=[(20, 5)]))
    for ano in range(2010, 2025):
        secos = [(30, 12), (60, 15), (90, 9)]  # 12 e 15 dias contam; 9 não
        esperado["B"].append(plantar(df, f"{ano}-11-05", f"{ano + 1}-03-10", secos=secos, quentes=[(5, 12)]))
    # dias quentes fora da estação não contam
    for ano in range(1995, 2025):
        faixa(df, f"{ano}-06-01", f"{ano}-06-20", "tmax", 37.0)
    return esperado


def test_medias_por_periodo(ponto):
    esperado = cenario_mudanca(ponto["serie"])
    r = clima.clima_mudou(-17.8, -50.92, "pt")
    assert r["modo"] == "estacao"
    a, b = r["periodos"]["1995-2009"], r["periodos"]["2010-2025"]
    assert a["chuva_mm"] == pytest.approx(sum(esperado["A"]) / 15)
    assert b["chuva_mm"] == pytest.approx(sum(esperado["B"]) / 15)
    assert (a["inicio"], a["fim"], b["inicio"], b["fim"]) == ("10-15", "03-31", "11-05", "03-10")
    assert (a["veranicos"], b["veranicos"]) == (0, 2)
    assert (a["dias_35c"], b["dias_35c"]) == (5, 12)


def test_inicio_da_estacao():
    df = base()
    faixa(df, "2000-07-25", "2000-07-27", "chuva", 10.0)  # antes de 1º/ago: ignorada
    faixa(df, "2000-09-01", "2000-09-03", "chuva", 7.0)  # seguida de 10 dias secos: falso início
    faixa(df, "2000-09-14", "2000-09-14", "chuva", 5.0)
    plantar(df, "2000-10-15", "2001-03-31")
    assert clima.estacao(df, 2000, "S")[0] == pd.Timestamp("2000-10-15")
    # 9 dias secos depois do pico de chuva não impedem o início
    df = base()
    faixa(df, "2000-09-01", "2000-09-03", "chuva", 7.0)
    faixa(df, "2000-09-13", "2000-12-31", "chuva", 1.0)
    assert clima.estacao(df, 2000, "S")[0] == pd.Timestamp("2000-09-01")
    # 19,98 mm em 3 dias não bastam; 20,01 mm bastam
    for mm, esperado in ((6.66, None), (6.67, pd.Timestamp("2000-09-01"))):
        df = base()
        faixa(df, "2000-08-01", "2001-07-31", "chuva", 1.0)
        faixa(df, "2000-09-01", "2000-09-03", "chuva", mm)
        e = clima.estacao(df, 2000, "S")
        assert (e and e[0]) == esperado
    # hemisfério N: referência 1º/fev
    df = base()
    faixa(df, "2000-01-20", "2000-01-22", "chuva", 10.0)
    plantar(df, "2000-06-20", "2000-09-30")
    assert clima.estacao(df, 2000, "N") == (pd.Timestamp("2000-06-20"), pd.Timestamp("2000-09-30"))


def test_fim_da_estacao():
    df = base()
    plantar(df, "2000-10-15", "2001-03-31")
    faixa(df, "2001-04-25", "2001-04-25", "chuva", 5.0)  # 5 mm em 10 dias: não estende
    assert clima.estacao(df, 2000, "S")[1] == pd.Timestamp("2001-03-31")
    faixa(df, "2001-05-10", "2001-05-10", "chuva", 10.0)  # 10 mm acumulados até 19/mai
    assert clima.estacao(df, 2000, "S")[1] == pd.Timestamp("2001-05-19")


def test_conta_veranicos(ponto):
    df = ponto["serie"]
    for ano in range(1995, 2025):
        plantar(df, f"{ano}-10-15", f"{ano + 1}-03-31", secos=[(31, 10), (50, 9), (70, 14), (100, 3)])
    r = clima.clima_mudou(-17.8, -50.92, "pt")
    assert r["periodos"]["1995-2009"]["veranicos"] == 2
    assert r["periodos"]["2010-2025"]["veranicos"] == 2


def test_anos_sem_estacao(ponto):
    df = ponto["serie"]
    a = [plantar(df, f"{ano}-10-15", f"{ano + 1}-03-31") for ano in range(1995, 2010)]
    b = [plantar(df, f"{ano}-10-20", f"{ano + 1}-01-31") for ano in range(2010, 2015)]
    r = clima.clima_mudou(-17.8, -50.92, "pt")
    assert r["anos_sem_estacao"] == 11  # 2015–2025
    assert r["modo"] == "estacao"
    assert r["periodos"]["1995-2009"]["chuva_mm"] == pytest.approx(sum(a) / 15)
    assert r["periodos"]["2010-2025"]["chuva_mm"] == pytest.approx(sum(b) / 5)
    assert r["periodos"]["2010-2025"]["inicio"] == "10-20"


def test_modo_anual(ponto):
    df = ponto["serie"]
    for ano in range(1995, 2004):  # 9 anos com estação
        plantar(df, f"{ano}-10-15", f"{ano + 1}-03-31")
    for ano in range(1995, 2026):
        faixa(df, f"{ano}-06-01", f"{ano}-06-01", "chuva", 5.0)
        faixa(df, f"{ano}-12-01", f"{ano}-12-0{3 if ano < 2010 else 7}", "tmax", 36.0)
    r = clima.clima_mudou(-17.8, -50.92, "pt")
    assert r["modo"] == "anual" and r["anos_sem_estacao"] == 22
    anual = df.groupby(df["data"].dt.year)["chuva"].sum()
    a, b = r["periodos"]["1995-2009"], r["periodos"]["2010-2025"]
    assert a["chuva_mm"] == pytest.approx(anual.loc[1995:2009].mean())
    assert b["chuva_mm"] == pytest.approx(anual.loc[2010:2025].mean())
    assert (a["dias_35c"], b["dias_35c"]) == (3, 7)
    assert "inicio" not in a
    # com 10 anos de estação volta ao modo estação
    plantar(df, "2004-10-15", "2005-03-31")
    assert clima.clima_mudou(-17.8, -50.92, "pt")["modo"] == "estacao"


def test_resumo_no_idioma(ponto):
    cenario_mudanca(ponto["serie"])
    # maior mudança relativa: veranicos 0 -> 2
    assert clima.clima_mudou(-17.8, -50.92, "pt")["resumo"] == "O número de veranicos passou de 0.0 em 1995–2009 para 2.0 em 2010–2025."
    assert clima.clima_mudou(-17.8, -50.92, "en")["resumo"] == "The number of dry spells went from 0.0 in 1995–2009 to 2.0 in 2010–2025."
    assert clima.clima_mudou(-17.8, -50.92, "es")["resumo"] == "El número de veranillos pasó de 0.0 en 1995–2009 a 2.0 en 2010–2025."
    assert clima.clima_mudou(-17.8, -50.92, "fr")["resumo"] == clima.clima_mudou(-17.8, -50.92, "en")["resumo"]


def test_chuva_por_ano(ponto):
    df = ponto["serie"]
    for ano in range(1995, 2026):
        faixa(df, f"{ano}-06-15", f"{ano}-06-15", "chuva", float(ano - 1900))
        faixa(df, f"{ano}-12-31", f"{ano}-12-31", "chuva", 100.0)
    df.loc[10, "chuva"] = float("nan")  # NaN conta como 0
    r = clima.clima_mudou(-17.8, -50.92, "pt")["chuva_por_ano"]
    assert len(r) == 31
    assert r == [{"ano": a, "chuva_mm": float(a - 1900 + 100)} for a in range(1995, 2026)]


FIXTURE_CULTURAS = Path(__file__).resolve().parent.parent / "fixtures" / "culturas.csv"
DATAS_36 = [f"{m:02d}-{d:02d}" for m in range(1, 13) for d in (1, 11, 21)]


@pytest.fixture
def janela(ponto, monkeypatch):
    """Ponto com simulação falsa: a data MM-DD quebra nos `quebras[MM-DD]` primeiros anos desde 1995."""
    monkeypatch.setattr(culturas, "CSV", FIXTURE_CULTURAS)  # cultura "Teste": t_min_c = 10
    monkeypatch.setattr(solo, "agua_disponivel", lambda lat, lon: {"cad_mm": 100, "argila_pct": None, "areia_pct": None, "fonte": "padrão"})
    ponto["quebras"], ponto["anos"] = {}, set()

    def falso(serie, cultura, cad_mm, inicio, lat):
        ponto["anos"].add(inicio.year)
        n = ponto["quebras"].get(inicio.strftime("%m-%d"), 0)
        return {"perda": 0.0, "quebra": inicio.year - 1995 < n, "eta": 0.0, "etc": 0.0}

    monkeypatch.setattr(balanco, "simular_safra", falso)
    return ponto


def test_janela_decendios(janela):
    janela["quebras"] = {"03-11": 9, "07-21": 30, "12-01": 1}
    r = clima.janela_plantio(-17.8, -50.92, "Teste")
    assert [d["data"] for d in r["datas"]] == DATAS_36
    risco = {d["data"]: d["risco_pct"] for d in r["datas"]}
    assert (risco["03-11"], risco["07-21"], risco["12-01"], risco["01-01"]) == (30, 100, 3, 0)
    assert janela["anos"] == set(range(1995, 2025))


def test_janela_frio(janela, monkeypatch):
    df = janela["serie"]
    for ano in range(1995, 2026):
        faixa(df, f"{ano}-06-01", f"{ano}-08-31", "tmin", 5.0)  # resto do ano: 18 °C
    r = clima.janela_plantio(-17.8, -50.92, "Teste")
    frio = [d["data"] for d in r["datas"] if d["motivo"] == "frio"]
    # 21/mai: 11 dias a 18 °C e 19 a 5 °C -> 9,8 °C < 10; 21/ago: 11 a 5 °C e 19 a 18 °C -> 13,2 °C
    assert frio == ["05-21", "06-01", "06-11", "06-21", "07-01", "07-11", "07-21", "08-01", "08-11"]
    assert all(d["risco_pct"] == 100 for d in r["datas"] if d["motivo"] == "frio")
    assert all(d["risco_pct"] == 0 and d["motivo"] is None for d in r["datas"] if d["data"] not in frio)
    # sem t_min_c não há corte por frio
    sem_t = {**culturas.carregar(FIXTURE_CULTURAS)["Teste"], "t_min_c": None}
    monkeypatch.setattr(culturas, "carregar", lambda path=None: {"Teste": sem_t})
    assert all(d["motivo"] is None and d["risco_pct"] == 0 for d in clima.janela_plantio(-17.8, -50.92, "Teste")["datas"])


def test_janela_fim_seguro(janela):
    # inseguras (≥ 20%) em todo o ano, exceto 01/mar–21/mai (9 datas) e 11/out–11/nov (4 datas)
    q = {d: 15 for d in DATAS_36}
    for d in ["03-01", "03-11", "03-21", "04-01", "04-11", "04-21", "05-01", "05-11", "05-21", "10-11", "10-21", "11-01", "11-11"]:
        q[d] = 5  # 17%
    janela["quebras"] = q
    assert clima.janela_plantio(-17.8, -50.92, "Teste")["fim_seguro"] == "05-21"
    # risco de exatamente 20% (6 de 30) não é seguro: sobra 01/mar–21/abr (6 datas), maior que a de outubro (4)
    q["05-01"] = 6
    assert clima.janela_plantio(-17.8, -50.92, "Teste")["fim_seguro"] == "04-21"
    # sequência que cruza o ano (21/nov–21/jan, 7 datas) vence a de março–abril (6)
    for d in ["11-21", "12-01", "12-11", "12-21", "01-01", "01-11", "01-21"]:
        q[d] = 0
    for d in ["10-11", "10-21", "11-01", "11-11"]:
        q[d] = 15
    assert clima.janela_plantio(-17.8, -50.92, "Teste")["fim_seguro"] == "01-21"


def test_janela_sem_data_segura(janela):
    janela["quebras"] = {d: 6 for d in DATAS_36}  # 20% em todas: nenhuma < 20
    r = clima.janela_plantio(-17.8, -50.92, "Teste")
    assert r["fim_seguro"] is None
    assert {d["risco_pct"] for d in r["datas"]} == {20}


def test_temporada_incompleta_fora_das_medias(ponto):
    df = ponto["serie"]
    b = [plantar(df, f"{ano}-10-15", f"{ano + 1}-03-31") for ano in range(2010, 2025)]
    for ano in range(1995, 2010):
        plantar(df, f"{ano}-10-15", f"{ano + 1}-03-31")
    for ultimo in ("2025-12-31", "2025-12-18", "2025-12-02"):  # menos de 30 dias de série depois do fim
        faixa(df, "2025-08-01", "2025-12-31", "chuva", 0.0)
        plantar(df, "2025-10-15", ultimo)
        r = clima.clima_mudou(-17.8, -50.92, "pt")
        assert r["anos_sem_estacao"] == 1, ultimo
        assert r["periodos"]["2010-2025"]["chuva_mm"] == pytest.approx(sum(b) / 15)
    faixa(df, "2025-08-01", "2025-12-31", "chuva", 0.0)
    for ultimo in ("2025-11-30", "2025-12-01"):  # 31 e exatamente 30 dias depois do fim: conta
        faixa(df, "2025-08-01", "2025-12-31", "chuva", 0.0)
        plantar(df, "2025-10-15", ultimo)
        assert clima.clima_mudou(-17.8, -50.92, "pt")["anos_sem_estacao"] == 0, ultimo


def test_janela_marca_preliminar(janela, monkeypatch):
    # fixture "Teste" não tem coluna validado: conta como não validada
    assert clima.janela_plantio(-17.8, -50.92, "Teste")["preliminar"] is True
    real = culturas.carregar
    monkeypatch.setattr(culturas, "carregar", lambda path=None: {k: {**v, "validado": "true"} for k, v in real(path).items()})
    assert clima.janela_plantio(-17.8, -50.92, "Teste")["preliminar"] is False
