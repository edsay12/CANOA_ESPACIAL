"""Camada 1 (global): ranking de culturas para uma safra e planos de rotação de 3 anos.

Contratos: ranking_safra(lat, lon, data_semeadura, prioridades, idioma) · planos_rotacao(lat, lon, historico, prioridades, idioma)
Ambos devolvem {itens, culturas_ignoradas, fontes}.
"""

from itertools import product

import pandas as pd

from core import balanco, contexto, culturas, power, solo, textos, validacao

ANOS = range(1995, 2025)
ANTES, DEPOIS = range(1995, 2010), range(2010, 2025)
PAPEIS_ROTACAO = {"Segunda safra", "Inverno", "Cobertura"}
MAX_CANDIDATAS = 5
JANELAS = range(ANOS[0], ANOS[-1] - 1)  # 1995–2022: cada janela cobre 3 anos até 2024
# SPEC_DEVIATION: a spec não diz a data de semeadura dos planos; padrão 03-01 (safrinha do Cerrado, igual ao site)
# no hemisfério S e 09-01 (mesma época, 6 meses depois) no N; o chamador pode passar `data_semeadura`.
SEMEADURA_PLANOS = {"S": "03-01", "N": "09-01"}


def _perdas(serie, c, cad_mm, lat, mes, dia):
    """Ano de semeadura -> perda estimada, uma simulação por ano de 1995 a 2024."""
    return {a: balanco.simular_safra(serie, c, cad_mm, pd.Timestamp(a, mes, dia), lat)["perda"] for a in ANOS}


def _retorno(ctx, nome, perda_media):
    """produtividade × (1 − perda média) × preço na moeda do contexto, ou None sem dado."""
    p = ctx["produtividade"].get(nome)
    return None if p is None else p["produtividade_t_ha"] * (1 - perda_media) * p["preco_t"]


def _notas(itens, pesos, chave="retorno"):
    """Grava `nota` (0–100) em cada item a partir de risco_pct, nota_solo e `chave` (retorno); ordena por nota."""
    retornos = [i[chave] for i in itens if i[chave] is not None]
    if not retornos:
        resto = pesos["seguranca"] + pesos["solo"]
        # só retorno pedido e nenhum retorno disponível: não há o que reescalar, as notas ficam 0
        pesos = {"retorno": 0.0, "seguranca": pesos["seguranca"] / resto, "solo": pesos["solo"] / resto} if resto else {k: 0.0 for k in pesos}
    maior = max(retornos, default=0)
    for i in itens:
        seguranca = 100 - i["risco_pct"]
        # shortcut: nota_solo vazia no CSV vale 3 (neutra, 50 pontos); remover quando o CSV estiver completo
        solo_n = (float(i["nota_solo"] if i["nota_solo"] is not None else 3) - 1) / 4 * 100
        ret = 100 * i[chave] / maior if i[chave] is not None and maior > 0 else 0.0
        i["nota"] = round(pesos["seguranca"] * seguranca + pesos["solo"] * solo_n + pesos["retorno"] * ret, 1)
    itens.sort(key=lambda i: i["nota"], reverse=True)
    return itens


def ranking_safra(lat, lon, data_semeadura, prioridades=None, idioma="pt"):
    mes, dia = validacao.data_mmdd(data_semeadura)
    pesos = validacao.pesos(prioridades)
    ctx = contexto.contexto(lat, lon)
    serie = power.serie(lat, lon)
    cad = solo.agua_disponivel(lat, lon)["cad_mm"]
    todas = culturas.carregar()

    itens, ignoradas = [], []
    for nome in ctx["culturas"]:
        c = todas[nome]
        if not culturas.completa(c):
            ignoradas.append(nome)
            continue
        perdas = _perdas(serie, c, cad, lat, mes, dia)
        quebra = {a: p > balanco.LIMITE_QUEBRA for a, p in perdas.items()}
        n = sum(quebra.values())
        itens.append({
            "cultura": nome,
            "risco_pct": round(100 * n / len(ANOS)),
            "anos_quebra": f"{n}/{len(ANOS)}",
            "nota_solo": c["nota_solo"],
            "retorno": _retorno(ctx, nome, sum(perdas.values()) / len(perdas)),
            "moeda": ctx["moeda"],
            "preliminar": culturas.preliminar(c),
            "explicacao": textos.t(
                "explicacao_safra", idioma,
                depois=sum(quebra[a] for a in DEPOIS), n_depois=len(DEPOIS),
                antes=sum(quebra[a] for a in ANTES), n_antes=len(ANTES),
            ),
        })
    return {"itens": _notas(itens, pesos), "culturas_ignoradas": ignoradas, "fontes": ctx["fontes"]}


def _fixa_n(c):
    return str(c.get("fixa_n")).lower() == "true"


def _nota_solo_plano(cs):
    """Média de diversidade de famílias (1/3/5), leguminosa (5 ou 1) e nota_solo média das culturas."""
    diversidade = {1: 1, 2: 3}.get(len({c["familia"] for c in cs}), 5)
    leguminosa = 5 if any(_fixa_n(c) for c in cs) else 1
    media = sum(float(c["nota_solo"] if c["nota_solo"] is not None else 3) for c in cs) / len(cs)  # mesmo atalho do ranking
    return round((diversidade + leguminosa + media) / 3, 2)


def planos_rotacao(lat, lon, historico, prioridades=None, idioma="pt", data_semeadura=None):
    todas = culturas.carregar()
    desconhecidas = [c for c in historico if c not in todas]
    if desconhecidas:
        raise ValueError(f"culturas fora do culturas.csv: {desconhecidas}")
    if len(historico) < 3:
        raise ValueError("historico precisa de pelo menos 3 safras")
    atual = tuple(historico[-3:])
    sem_params = sorted({c for c in atual if not culturas.completa(todas[c])})
    if sem_params:
        raise ValueError(f"culturas do histórico sem parâmetros do modelo: {sem_params}")
    pesos = validacao.pesos(prioridades)
    if data_semeadura is not None:
        validacao.data_mmdd(data_semeadura)
    ctx = contexto.contexto(lat, lon)
    mes, dia = validacao.data_mmdd(data_semeadura or SEMEADURA_PLANOS[ctx["pais"]["hemisferio"]])
    serie = power.serie(lat, lon)
    cad = solo.agua_disponivel(lat, lon)["cad_mm"]

    papel = [n for n in ctx["culturas"] if todas[n].get("papel") in PAPEIS_ROTACAO]
    ignoradas = [n for n in papel if not culturas.completa(todas[n])]
    candidatas = [n for n in papel if n not in ignoradas][:MAX_CANDIDATAS]

    perdas = {n: _perdas(serie, todas[n], cad, lat, mes, dia) for n in dict.fromkeys([*candidatas, *atual])}  # uma vez por (cultura, ano)
    retorno = {n: _retorno(ctx, n, sum(p.values()) / len(p)) for n, p in perdas.items()}

    planos = []
    combinacoes = list(product(candidatas, repeat=3))
    for plano in combinacoes + ([] if atual in combinacoes else [atual]):
        quebras = sum(perdas[c][w + k] > balanco.LIMITE_QUEBRA for w in JANELAS for k, c in enumerate(plano))
        rets = [retorno[c] for c in plano]
        planos.append({
            "plano": list(plano),
            "risco_pct": round(100 * quebras / (3 * len(JANELAS))),
            "nota_solo": _nota_solo_plano([todas[c] for c in plano]),
            "retorno_ano": None if None in rets else sum(rets) / 3,
            "moeda": ctx["moeda"],
            "atual": plano == atual,
            "preliminar": any(culturas.preliminar(todas[c]) for c in plano),
            "explicacao": None,
        })
    _notas(planos, pesos, "retorno_ano")
    plano_atual = next(p for p in planos if p["atual"])
    itens = sorted([p for p in planos if not p["atual"]][:3] + [plano_atual], key=lambda p: p["nota"], reverse=True)
    for p in itens:
        if p["atual"]:
            continue
        risco = p["risco_pct"] - plano_atual["risco_pct"]
        if p["retorno_ano"] is None or plano_atual["retorno_ano"] is None:
            p["explicacao"] = textos.t("explicacao_plano_sem_retorno", idioma, risco=risco)
        else:
            dif = p["retorno_ano"] - plano_atual["retorno_ano"]
            p["explicacao"] = textos.t("explicacao_plano", idioma, risco=risco, retorno=dif, moeda=ctx["moeda"])
    return {"itens": itens, "culturas_ignoradas": ignoradas, "fontes": ctx["fontes"]}
