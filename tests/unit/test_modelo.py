import pandas as pd
import pytest

from core import balanco, contexto, culturas, modelo, power, solo

ANOS = list(range(1995, 2025))
PARAMS = {"dias_ini": 20, "dias_des": 30, "dias_mid": 40, "dias_fim": 20, "kc_ini": 0.3, "kc_mid": 1.2,
          "kc_fim": 0.6, "raiz_m": 1.0, "p_deplecao": 0.55, "ky": 1.25}


def cultura(nome, familia="Poaceae", fixa_n=False, nota_solo=3, papel="Segunda safra", **extra):
    return {"cultura": nome, "papel": papel, "familia": familia, "fixa_n": fixa_n, "nota_solo": nota_solo, **PARAMS, **extra}


@pytest.fixture
def ponto(monkeypatch):
    """Ponto falso: perda por (cultura, ano de semeadura) em `perdas` (padrão 0); chamadas em `chamadas`."""
    estado = {
        "culturas": {
            "A": cultura("A", nota_solo=5),
            "B": cultura("B", nota_solo=1),
            "C": cultura("C", nota_solo=3),
            "D": {**cultura("D"), "dias_mid": None},
        },
        "ctx": {
            "pais": {"iso2": "BR", "nome": "Brazil", "hemisferio": "S"},
            "culturas": ["B", "C", "A"],
            "fontes": ["NASA POWER", "SoilGrids", "FAOSTAT"],
            "nivel_precisao": "pais",
            "classe_climatica": "tropical",
            "produtividade": {"A": {"produtividade_t_ha": 10.0, "preco_t": 100.0}, "B": {"produtividade_t_ha": 10.0, "preco_t": 100.0}},
            "moeda": "USD",
        },
        "perdas": {},
        "chamadas": [],
    }
    monkeypatch.setattr(culturas, "carregar", lambda path=None: estado["culturas"])
    monkeypatch.setattr(contexto, "contexto", lambda lat, lon: estado["ctx"])
    monkeypatch.setattr(power, "serie", lambda lat, lon: pd.DataFrame())
    monkeypatch.setattr(solo, "agua_disponivel", lambda lat, lon: {"cad_mm": 100, "argila_pct": None, "areia_pct": None, "fonte": "SoilGrids"})

    def falso(serie, c, cad_mm, inicio, lat):
        estado["chamadas"].append((c["cultura"], inicio))
        perda = estado["perdas"].get((c["cultura"], inicio.year), 0.0)
        return {"perda": perda, "quebra": perda > 0.20, "eta": 0.0, "etc": 0.0}

    monkeypatch.setattr(balanco, "simular_safra", falso)
    return estado


def quebrar(estado, nome, anos, perda=1.0):
    for a in anos:
        estado["perdas"][(nome, a)] = perda


def por_cultura(r):
    return {i["cultura"]: i for i in r["itens"]}


def test_simula_1995_a_2024(ponto):
    modelo.ranking_safra(-17.8, -50.92, "03-15")
    for nome in ("A", "B", "C"):
        inicios = [i for c, i in ponto["chamadas"] if c == nome]
        assert inicios == [pd.Timestamp(a, 3, 15) for a in ANOS]
    assert len(ponto["chamadas"]) == 3 * 30


def test_risco_e_anos_quebra(ponto):
    quebrar(ponto, "A", range(1995, 2002))  # 7 quebras
    quebrar(ponto, "A", [2005], perda=0.20)  # exatamente 20%: não é quebra
    quebrar(ponto, "C", ANOS)
    r = por_cultura(modelo.ranking_safra(-17.8, -50.92, "03-15"))
    assert (r["A"]["risco_pct"], r["A"]["anos_quebra"]) == (23, "7/30")
    assert (r["B"]["risco_pct"], r["B"]["anos_quebra"]) == (0, "0/30")
    assert (r["C"]["risco_pct"], r["C"]["anos_quebra"]) == (100, "30/30")


def test_nota_e_ordenacao(ponto):
    quebrar(ponto, "B", range(1995, 2010))  # risco 50, perda média 0,5
    r = modelo.ranking_safra(-17.8, -50.92, "03-15")
    # pesos 0,4 retorno · 0,4 segurança · 0,2 solo
    # A: retorno 1000 (maior) -> 100, segurança 100, solo 5 -> 100: nota 100
    # C: sem retorno -> 0, segurança 100, solo 3 -> 50: nota 50
    # B: retorno 500 -> 50, segurança 50, solo 1 -> 0: nota 40
    assert [(i["cultura"], i["nota"]) for i in r["itens"]] == [("A", 100.0), ("C", 50.0), ("B", 40.0)]
    itens = por_cultura(r)
    assert (itens["A"]["retorno"], itens["B"]["retorno"], itens["C"]["retorno"]) == (pytest.approx(1000), pytest.approx(500), None)
    # só segurança: A e C empatam em 100, B fica com 50
    r = modelo.ranking_safra(-17.8, -50.92, "03-15", {"seguranca": 3})
    assert [i["nota"] for i in r["itens"]] == [100.0, 100.0, 50.0]
    assert r["itens"][-1]["cultura"] == "B"


def test_sem_retorno_reescala_pesos(ponto):
    ponto["ctx"]["produtividade"], ponto["ctx"]["moeda"] = {}, None
    quebrar(ponto, "B", range(1995, 2010))
    r = por_cultura(modelo.ranking_safra(-17.8, -50.92, "03-15"))
    # segurança 0,4/0,6 = 2/3 e solo 0,2/0,6 = 1/3
    assert r["A"]["nota"] == 100.0
    assert r["C"]["nota"] == pytest.approx(2 / 3 * 100 + 1 / 3 * 50, abs=0.05)
    assert r["B"]["nota"] == pytest.approx(2 / 3 * 50, abs=0.05)
    assert all(i["retorno"] is None for i in r.values())


def test_explicacao_antes_e_depois(ponto):
    quebrar(ponto, "A", [1995, 1999, 2003, 2007])
    quebrar(ponto, "A", [2010, 2011, 2013, 2015, 2017, 2019, 2020, 2022, 2024])
    pt = por_cultura(modelo.ranking_safra(-17.8, -50.92, "03-15", idioma="pt"))["A"]["explicacao"]
    assert pt == "faltou água em 9 de 15 anos desde 2010; antes eram 4 de 15"
    en = por_cultura(modelo.ranking_safra(-17.8, -50.92, "03-15", idioma="en"))["A"]["explicacao"]
    assert "9 of 15" in en and "4 of 15" in en and "2010" in en
    es = por_cultura(modelo.ranking_safra(-17.8, -50.92, "03-15", idioma="es"))["A"]["explicacao"]
    assert es.startswith("faltó agua en 9 de 15")
    assert por_cultura(modelo.ranking_safra(-17.8, -50.92, "03-15", idioma="fr"))["A"]["explicacao"] == en


def test_cultura_sem_parametros_ignorada(ponto):
    ponto["ctx"]["culturas"] = ["B", "D", "A"]
    r = modelo.ranking_safra(-17.8, -50.92, "03-15")
    assert {i["cultura"] for i in r["itens"]} == {"A", "B"}
    assert r["culturas_ignoradas"] == ["D"]
    assert all(c != "D" for c, _ in ponto["chamadas"])


def test_formato_saida_ranking(ponto):
    r = modelo.ranking_safra(-17.8, -50.92, "03-15")
    assert set(r) == {"itens", "culturas_ignoradas", "fontes"}
    assert r["fontes"] == ["NASA POWER", "SoilGrids", "FAOSTAT"]
    assert r["culturas_ignoradas"] == []
    campos = {"cultura", "nota", "risco_pct", "anos_quebra", "nota_solo", "retorno", "moeda", "explicacao"}
    assert len(r["itens"]) == 3 and all(set(i) == campos for i in r["itens"])
    assert {i["moeda"] for i in r["itens"]} == {"USD"}
    assert all(0 <= i["nota"] <= 100 for i in r["itens"])


# --- planos de rotação ---


@pytest.fixture
def rotacao(ponto):
    """Candidatas de rotação: A (nunca quebra), C (sempre quebra) e F (leguminosa); P é Principal (fora)."""
    ponto["culturas"].update({
        "C": cultura("C", nota_solo=3),
        "F": cultura("F", familia="Fabaceae", fixa_n=True, nota_solo=5, papel="Cobertura"),
        "G": cultura("G", familia="Asteraceae", nota_solo=4, papel="Inverno"),
        "P": cultura("P", papel="Principal"),
    })
    ponto["ctx"]["culturas"] = ["A", "C", "P"]
    ponto["ctx"]["produtividade"] = {n: {"produtividade_t_ha": 10.0, "preco_t": 100.0} for n in ("A", "C", "F", "G", "P")}
    quebrar(ponto, "C", ANOS)
    return ponto


def plano(r, seq):
    return next(p for p in r["itens"] if p["plano"] == list(seq))


def test_planos_combinacoes_max_5(rotacao):
    for n, fam in [("H", "Brassicaceae"), ("X", "Malvaceae"), ("Y", "Malvaceae")]:
        rotacao["culturas"][n] = cultura(n, familia=fam, nota_solo=5, papel="Cobertura")
    rotacao["culturas"]["A"]["nota_solo"] = 1
    rotacao["culturas"]["G"]["nota_solo"] = 5
    # 5 primeiras candidatas: A, B, F, G, H; X e Y passam do limite; P é Principal
    rotacao["ctx"]["culturas"] = ["A", "P", "B", "F", "G", "H", "X", "Y"]
    r = modelo.planos_rotacao(-17.8, -50.92, ["A", "A", "A"], {"solo": 1})
    assert {c for c, _ in rotacao["chamadas"]} == {"A", "B", "F", "G", "H"}
    # só solo: só F, G e H juntam 3 famílias, leguminosa e nota 5; qualquer plano com A ou B (nota 1) fica abaixo
    melhores = [p for p in r["itens"] if not p["atual"]]
    assert len(melhores) == 3
    assert all(sorted(p["plano"]) == ["F", "G", "H"] for p in melhores)
    assert len({tuple(p["plano"]) for p in melhores}) == 3


def test_planos_janelas_3_anos(rotacao):
    rotacao["ctx"]["culturas"] = ["A", "B"]
    quebrar(rotacao, "A", [1995, 2024])
    # janelas 1995–1997 … 2022–2024 (28) × 3 safras = 84; 1995 só cai na 1ª posição e 2024 só na 3ª
    r = modelo.planos_rotacao(-17.8, -50.92, ["A", "B", "A"])
    assert plano(r, "ABA")["risco_pct"] == round(100 * 2 / 84)
    r = modelo.planos_rotacao(-17.8, -50.92, ["B", "A", "B"])
    assert plano(r, "BAB")["risco_pct"] == 0
    r = modelo.planos_rotacao(-17.8, -50.92, ["A", "A", "B"])
    assert plano(r, "AAB")["risco_pct"] == round(100 * 1 / 84)
    # cada (cultura, ano) é simulado uma vez só, de 1995 a 2024
    anos = sorted(i.year for c, i in rotacao["chamadas"][:60])
    assert anos == sorted(ANOS * 2)


def test_planos_nota_solo(rotacao):
    # A, C: Poaceae nota 3 (C) / 5 (A); F: Fabaceae leguminosa nota 5; G: Asteraceae nota 4
    r = modelo.planos_rotacao(-17.8, -50.92, ["C", "C", "C"])
    assert plano(r, "CCC")["nota_solo"] == pytest.approx((1 + 1 + 3) / 3, abs=0.01)
    r = modelo.planos_rotacao(-17.8, -50.92, ["C", "F", "C"])
    assert plano(r, "CFC")["nota_solo"] == pytest.approx((3 + 5 + 11 / 3) / 3, abs=0.01)
    r = modelo.planos_rotacao(-17.8, -50.92, ["C", "F", "G"])
    assert plano(r, "CFG")["nota_solo"] == pytest.approx((5 + 5 + 4) / 3, abs=0.01)


def test_planos_inclui_atual(rotacao):
    r = modelo.planos_rotacao(-17.8, -50.92, ["A", "C", "C", "C"])
    atuais = [p for p in r["itens"] if p["atual"]]
    assert len(atuais) == 1 and atuais[0]["plano"] == ["C", "C", "C"]
    assert atuais[0]["risco_pct"] == 100
    assert all(p["nota"] > atuais[0]["nota"] for p in r["itens"] if not p["atual"])
    # atual com cultura fora das candidatas (Principal) também aparece
    r = modelo.planos_rotacao(-17.8, -50.92, ["P", "P", "P"])
    assert [p["plano"] for p in r["itens"] if p["atual"]] == [["P", "P", "P"]]


def test_planos_top3_mais_atual(rotacao):
    r = modelo.planos_rotacao(-17.8, -50.92, ["C", "C", "C"], {"seguranca": 1})
    assert len(r["itens"]) == 4 and sum(p["atual"] for p in r["itens"]) == 1
    # só segurança: AAA (risco 0) e depois os planos com um C (risco 33); CCC fica por último
    assert [(p["risco_pct"], p["nota"]) for p in r["itens"]] == [(0, 100.0), (33, 67.0), (33, 67.0), (100, 0.0)]
    assert r["itens"][0]["plano"] == ["A", "A", "A"]
    assert set(r) == {"itens", "culturas_ignoradas", "fontes"}
    assert r["fontes"] == ["NASA POWER", "SoilGrids", "FAOSTAT"]
    campos = {"plano", "nota", "risco_pct", "nota_solo", "retorno_ano", "moeda", "atual", "explicacao"}
    assert all(set(p) == campos for p in r["itens"])


def test_planos_explicacao_vs_atual(rotacao):
    # A rende 10 t × 100 sem perda = 1000/ano; C perde tudo = 0
    r = modelo.planos_rotacao(-17.8, -50.92, ["C", "C", "C"], {"seguranca": 1}, "pt")
    aaa = plano(r, "AAA")
    assert aaa["retorno_ano"] == pytest.approx(1000)
    assert aaa["explicacao"] == "-100 pontos de risco e +1000 USD/ano de retorno frente ao plano atual"
    assert plano(r, "CCC")["explicacao"] is None
    en = plano(modelo.planos_rotacao(-17.8, -50.92, ["C", "C", "C"], {"seguranca": 1}, "en"), "AAA")["explicacao"]
    assert en == "-100 risk points and +1000 USD/year of return versus the current plan"
    es = plano(modelo.planos_rotacao(-17.8, -50.92, ["C", "C", "C"], {"seguranca": 1}, "es"), "AAA")["explicacao"]
    assert es.startswith("-100 puntos de riesgo y +1000 USD")
    # sem retorno: só a diferença de risco
    rotacao["ctx"]["produtividade"], rotacao["ctx"]["moeda"] = {}, None
    r = modelo.planos_rotacao(-17.8, -50.92, ["C", "C", "C"], {"seguranca": 1}, "pt")
    assert plano(r, "AAA")["explicacao"] == "-100 pontos de risco frente ao plano atual"


def test_planos_historico_invalido(rotacao):
    with pytest.raises(ValueError) as e:
        modelo.planos_rotacao(-17.8, -50.92, ["A", "Xyz", "Abc"])
    assert "Xyz" in str(e.value) and "Abc" in str(e.value) and "'A'" not in str(e.value)
    assert rotacao["chamadas"] == []
