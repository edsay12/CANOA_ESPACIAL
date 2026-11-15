"""Camada 1 (global): ranking de culturas para uma safra e planos de rotação de 3 anos.

Contratos: ranking_safra(lat, lon, data_semeadura, prioridades, idioma) · planos_rotacao(lat, lon, historico, prioridades, idioma)
Ambos devolvem {itens, culturas_ignoradas, fontes}.
"""

import pandas as pd

from core import balanco, contexto, culturas, power, solo, textos, validacao

ANOS = range(1995, 2025)
ANTES, DEPOIS = range(1995, 2010), range(2010, 2025)


def _perdas(serie, c, cad_mm, lat, mes, dia):
    """Ano de semeadura -> perda estimada, uma simulação por ano de 1995 a 2024."""
    return {a: balanco.simular_safra(serie, c, cad_mm, pd.Timestamp(a, mes, dia), lat)["perda"] for a in ANOS}


def _retorno(ctx, nome, perda_media):
    """produtividade × (1 − perda média) × preço na moeda do contexto, ou None sem dado."""
    p = ctx["produtividade"].get(nome)
    return None if p is None else p["produtividade_t_ha"] * (1 - perda_media) * p["preco_t"]


def _notas(itens, pesos):
    """Grava `nota` (0–100) em cada item a partir de risco_pct, nota_solo e retorno; ordena por nota."""
    retornos = [i["retorno"] for i in itens if i["retorno"] is not None]
    if not retornos:
        resto = pesos["seguranca"] + pesos["solo"]
        # só retorno pedido e nenhum retorno disponível: não há o que reescalar, as notas ficam 0
        pesos = {"retorno": 0.0, "seguranca": pesos["seguranca"] / resto, "solo": pesos["solo"] / resto} if resto else {k: 0.0 for k in pesos}
    maior = max(retornos, default=0)
    for i in itens:
        seguranca = 100 - i["risco_pct"]
        # shortcut: nota_solo vazia no CSV vale 3 (neutra, 50 pontos); remover quando o CSV estiver completo
        solo_n = (float(i["nota_solo"] if i["nota_solo"] is not None else 3) - 1) / 4 * 100
        ret = 100 * i["retorno"] / maior if i["retorno"] is not None and maior > 0 else 0.0
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
            "explicacao": textos.t(
                "explicacao_safra", idioma,
                depois=sum(quebra[a] for a in DEPOIS), n_depois=len(DEPOIS),
                antes=sum(quebra[a] for a in ANTES), n_antes=len(ANTES),
            ),
        })
    return {"itens": _notas(itens, pesos), "culturas_ignoradas": ignoradas, "fontes": ctx["fontes"]}
