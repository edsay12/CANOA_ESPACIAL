"""Camada 1 (global): estação chuvosa, veranicos, antes x depois de 2010, janela de plantio.

Contratos: clima_mudou(lat, lon, idioma) · janela_plantio(lat, lon, cultura) · estacao(serie, ano, hemisferio)
"""

import numpy as np
import pandas as pd

from core import balanco, culturas, pais, power, solo, textos

ANOS = range(1995, 2026)
PERIODOS = {"1995-2009": range(1995, 2010), "2010-2025": range(2010, 2026)}
MIN_ANOS_ESTACAO = 10
ANOS_SAFRA = range(1995, 2025)
DATAS_JANELA = [(m, d) for m in range(1, 13) for d in (1, 11, 21)]
RISCO_SEGURO = 20
SECO_MM, DIAS_VERANICO = 1.0, 10


def _referencia(ano, hemisferio):
    return pd.Timestamp(ano, 8 if hemisferio == "S" else 2, 1)


def _runs_secos(chuva):
    """Comprimentos das sequências de dias com < 1 mm."""
    runs, n = [], 0
    for seco in chuva < SECO_MM:
        if seco:
            n += 1
        elif n:
            runs.append(n)
            n = 0
    return runs + [n] if n else runs


def estacao(serie, ano, hemisferio):
    """(início, fim) da estação do ano-safra que começa na data de referência, ou None.

    SPEC_DEVIATION: recebe a série inteira e o ano (o design dizia `serie_ano`), para achar a referência.
    Início: 1º dia a partir da referência com ≥ 20 mm em 3 dias e sem 10 dias secos nos 30 dias seguintes.
    Fim: último dia, a partir do início, cuja chuva acumulada nos 10 dias até ele é ≥ 10 mm.
    """
    ref = _referencia(ano, hemisferio)
    janela = serie[(serie["data"] >= ref) & (serie["data"] < ref + pd.DateOffset(years=1))]
    chuva = janela["chuva"].fillna(0).to_numpy(float)
    datas = janela["data"].to_numpy()
    for i in range(len(chuva)):
        if chuva[i : i + 3].sum() >= 20 and max(_runs_secos(chuva[i + 1 : i + 31]), default=0) < DIAS_VERANICO:
            acumulada = pd.Series(chuva).rolling(10, min_periods=1).sum().to_numpy()
            fim = i + int(np.flatnonzero(acumulada[i:] >= 10)[-1])
            return pd.Timestamp(datas[i]), pd.Timestamp(datas[fim])
    return None


def _anual(serie):
    df = serie.assign(chuva=serie["chuva"].fillna(0), calor=serie["tmax"] >= 35)
    return df.groupby(df["data"].dt.year).agg(chuva_mm=("chuva", "sum"), dias_35c=("calor", "sum"))


def _media(valores):
    return float(np.mean(valores)) if valores else None


def _mmdd(hemisferio, offset):
    return None if offset is None else (_referencia(2001, hemisferio) + pd.Timedelta(days=round(offset))).strftime("%m-%d")


def _resumo(periodos, modo, idioma):
    """Frase com a variável de maior mudança relativa; datas pesam o deslocamento frente à duração da estação."""
    a, d = periodos["1995-2009"], periodos["2010-2025"]
    if modo == "anual":
        variaveis = {"chuva_mm": "var_chuva_anual", "dias_35c": "var_calor"}
    else:
        variaveis = {"chuva_mm": "var_chuva", "inicio": "var_inicio", "fim": "var_fim", "veranicos": "var_veranicos", "dias_35c": "var_calor"}
    fmt = {"chuva_mm": "{:.0f} mm", "veranicos": "{:.1f}", "dias_35c": "{:.1f}"}
    melhor, maior = None, -1.0
    for campo, chave in variaveis.items():
        data = campo in ("inicio", "fim")
        va, vd = (a.get("_" + campo), d.get("_" + campo)) if data else (a[campo], d[campo])
        if va is None or vd is None:
            continue
        base = max(a["_fim"] - a["_inicio"], 1) if data else (abs(va) or 1)
        if abs(vd - va) / base > maior:
            maior = abs(vd - va) / base
            melhor = (chave, a[campo], d[campo]) if data else (chave, fmt[campo].format(va), fmt[campo].format(vd))
    if melhor is None:
        return ""
    chave, antes, depois = melhor
    return textos.t("resumo_clima", idioma, variavel=textos.t(chave, idioma), antes=antes, depois=depois)


def clima_mudou(lat, lon, idioma="pt"):
    """Médias de 1995–2009 e 2010–2025 da estação chuvosa (ou do ano civil, no modo anual)."""
    hemisferio = pais.de(lat, lon)["hemisferio"]
    serie = power.serie(lat, lon)
    anual = _anual(serie)
    chuva_por_ano = [{"ano": a, "chuva_mm": round(float(anual.loc[a, "chuva_mm"]), 1) if a in anual.index else 0.0} for a in ANOS]

    estacoes = {}
    for ano in ANOS:
        e = estacao(serie, ano, hemisferio)
        if e is None:
            continue
        ini, fim = e
        s = serie[(serie["data"] >= ini) & (serie["data"] <= fim)]
        chuva = s["chuva"].fillna(0).to_numpy(float)
        ref = _referencia(ano, hemisferio)
        estacoes[ano] = {
            "chuva_mm": float(chuva.sum()),
            "_inicio": (ini - ref).days,
            "_fim": (fim - ref).days,
            "veranicos": sum(r >= DIAS_VERANICO for r in _runs_secos(chuva)),
            "dias_35c": int((s["tmax"] >= 35).sum()),
        }
    anos_sem = len(ANOS) - len(estacoes)
    modo = "anual" if len(estacoes) < MIN_ANOS_ESTACAO else "estacao"

    periodos = {}
    for nome, anos in PERIODOS.items():
        if modo == "anual":
            linhas = anual[anual.index.isin(list(anos))]
            periodos[nome] = {"chuva_mm": _media(list(linhas["chuva_mm"])), "dias_35c": _media(list(linhas["dias_35c"]))}
            continue
        vals = [estacoes[a] for a in anos if a in estacoes]
        p = {k: _media([v[k] for v in vals]) for k in ("chuva_mm", "_inicio", "_fim", "veranicos", "dias_35c")}
        p["inicio"], p["fim"] = _mmdd(hemisferio, p["_inicio"]), _mmdd(hemisferio, p["_fim"])
        periodos[nome] = p

    resumo = _resumo(periodos, modo, idioma)
    for p in periodos.values():
        for k in [k for k in p if k.startswith("_")]:
            del p[k]
    return {
        "modo": modo,
        "periodos": periodos,
        "anos_sem_estacao": anos_sem,
        "resumo": resumo,
        "chuva_por_ano": chuva_por_ano,
        "fontes": ["NASA POWER"],
    }


def _fim_seguro(datas):
    """Última data da maior sequência de datas com risco < 20; o ano é circular (21/dez segue para 01/jan)."""
    seguro = [d["risco_pct"] < RISCO_SEGURO for d in datas]
    n = len(seguro)
    if not any(seguro):
        return None
    if all(seguro):
        return datas[-1]["data"]
    inicio = seguro.index(False) + 1  # começa logo após uma data insegura para não partir uma sequência
    melhor, fim, run = 0, None, 0
    for k in range(inicio, inicio + n):
        if seguro[k % n]:
            run += 1
            if run > melhor:
                melhor, fim = run, datas[k % n]["data"]
        else:
            run = 0
    return fim


def janela_plantio(lat, lon, cultura):
    """Risco de quebra semeando nos dias 01, 11 e 21 de cada mês, de 1995 a 2024, e a data-limite segura."""
    c = culturas.carregar().get(cultura)
    if c is None:
        raise ValueError(f"cultura desconhecida: {cultura!r}")
    if not culturas.completa(c):
        raise ValueError(f"cultura sem parâmetros do modelo: {cultura!r}")
    serie = power.serie(lat, lon)
    s = solo.agua_disponivel(lat, lon)
    tmin = serie.set_index("data")["tmin"]
    datas = []
    for mes, dia in DATAS_JANELA:
        inicios = [pd.Timestamp(ano, mes, dia) for ano in ANOS_SAFRA]
        if c.get("t_min_c") is not None:
            frio = np.nanmean([tmin[i : i + pd.Timedelta(days=29)].mean() for i in inicios])
            if frio < float(c["t_min_c"]):
                datas.append({"data": f"{mes:02d}-{dia:02d}", "risco_pct": 100, "motivo": "frio"})
                continue
        quebras = sum(balanco.simular_safra(serie, c, s["cad_mm"], i, lat)["quebra"] for i in inicios)
        datas.append({"data": f"{mes:02d}-{dia:02d}", "risco_pct": round(100 * quebras / len(inicios)), "motivo": None})
    return {"cultura": cultura, "datas": datas, "fim_seguro": _fim_seguro(datas), "fontes": ["NASA POWER", s["fonte"]]}
