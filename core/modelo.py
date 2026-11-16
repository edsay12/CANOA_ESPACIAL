"""Camada 1 (global): ranking de culturas para uma safra e planos de rotação de 3 anos.

Contratos: ranking_safra(lat, lon, data_semeadura, prioridades, idioma) · planos_rotacao(lat, lon, historico, prioridades, idioma)
Ambos devolvem {itens, culturas_ignoradas, fontes}.
"""

from itertools import product

import pandas as pd

from core import balanco, clima, contexto, culturas, power, solo, textos, validacao

ANOS = range(1995, 2025)
ANTES, DEPOIS = range(1995, 2010), range(2010, 2025)
PAPEIS_ROTACAO = {"Segunda safra", "Inverno", "Cobertura"}
MAX_CANDIDATAS = 5
JANELAS = range(ANOS[0], ANOS[-1] - 1)  # 1995–2022: cada janela cobre 3 anos até 2024
# MOT-64: sem `data_semeadura`, os planos semeiam no início médio da estação 2010–2025; no modo anual, estas datas
SEMEADURA_SEM_ESTACAO = {"N": "05-01", "S": "11-01"}


_memo_perdas = {}  # shortcut: cresce sem limite enquanto o processo vive; trocar por LRU se o site atender milhares de pontos


def _perdas(serie, c, cad_mm, lat, mes, dia):
    """Ano de semeadura -> perda estimada, uma simulação por ano de 1995 a 2024.

    A simulação é a parte cara do ranking e não depende das prioridades: fica memorizada por série, cultura, solo e data.
    """
    chave = (int(pd.util.hash_pandas_object(serie, index=False).sum()), repr(sorted(c.items())), cad_mm, lat, mes, dia)
    if chave not in _memo_perdas:
        _memo_perdas[chave] = {a: balanco.simular_safra(serie, c, cad_mm, pd.Timestamp(a, mes, dia), lat)["perda"] for a in ANOS}
    return dict(_memo_perdas[chave])


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


def _semeadura_padrao(lat, lon, hemisferio):
    """MOT-64: início médio da estação 2010–2025 do ponto; no modo anual, 05-01 (N) ou 11-01 (S)."""
    c = clima.clima_mudou(lat, lon)
    inicio = c["periodos"]["2010-2025"].get("inicio") if c["modo"] == "estacao" else None
    return inicio or SEMEADURA_SEM_ESTACAO[hemisferio]


def _avaliar(plano, atual, perdas, retorno, todas, ctx):
    quebras = sum(perdas[c][w + k] > balanco.LIMITE_QUEBRA for w in JANELAS for k, c in enumerate(plano))
    rets = [retorno[c] for c in plano]
    return {
        "plano": list(plano),
        "risco_pct": round(100 * quebras / (3 * len(JANELAS))),
        "nota_solo": _nota_solo_plano([todas[c] for c in plano]),
        "retorno_ano": None if None in rets else sum(rets) / 3,
        "moeda": ctx["moeda"],
        "atual": tuple(plano) == atual,
        "preliminar": any(culturas.preliminar(todas[c]) for c in plano),
        "sem_parametros": False,
        "explicacao": None,
    }


def planos_rotacao(lat, lon, historico, prioridades=None, idioma="pt", data_semeadura=None):
    todas = culturas.carregar()
    desconhecidas = [c for c in historico if c not in todas]
    if desconhecidas:
        raise ValueError(f"culturas fora do culturas.csv: {desconhecidas}")
    if len(historico) < 3:
        raise ValueError("historico precisa de pelo menos 3 safras")
    atual = tuple(historico[-3:])
    sem_params = sorted({c for c in atual if not culturas.completa(todas[c])})  # MOT-65: planos saem sem comparar
    pesos = validacao.pesos(prioridades)
    if data_semeadura is not None:
        validacao.data_mmdd(data_semeadura)
    ctx = contexto.contexto(lat, lon)
    mes, dia = validacao.data_mmdd(data_semeadura or _semeadura_padrao(lat, lon, ctx["pais"]["hemisferio"]))
    serie = power.serie(lat, lon)
    cad = solo.agua_disponivel(lat, lon)["cad_mm"]

    papel = [n for n in ctx["culturas"] if todas[n].get("papel") in PAPEIS_ROTACAO]
    ignoradas = [n for n in papel if not culturas.completa(todas[n])]
    ignoradas += [n for n in sem_params if n not in ignoradas]
    candidatas = [n for n in papel if n not in ignoradas][:MAX_CANDIDATAS]

    perdas = {n: _perdas(serie, todas[n], cad, lat, mes, dia) for n in dict.fromkeys([*candidatas, *atual]) if n not in sem_params}  # uma vez por (cultura, ano)
    retorno = {n: _retorno(ctx, n, sum(p.values()) / len(p)) for n, p in perdas.items()}

    planos = []
    combinacoes = list(product(candidatas, repeat=3))
    for plano in combinacoes:
        planos.append(_avaliar(plano, atual, perdas, retorno, todas, ctx))
    if atual not in combinacoes:
        if sem_params:
            planos.append({"plano": list(atual), "risco_pct": None, "nota": None, "nota_solo": _nota_solo_plano([todas[c] for c in atual]),
                           "retorno_ano": None, "moeda": ctx["moeda"], "atual": True, "preliminar": True, "sem_parametros": True, "explicacao": None})
        else:
            planos.append(_avaliar(atual, atual, perdas, retorno, todas, ctx))
    _notas([p for p in planos if not p["sem_parametros"]], pesos, "retorno_ano")
    plano_atual = next(p for p in planos if p["atual"])
    melhores = sorted([p for p in planos if not p["atual"]], key=lambda p: p["nota"], reverse=True)[:3]
    itens = sorted(melhores + [plano_atual], key=lambda p: -1 if p["nota"] is None else p["nota"], reverse=True)
    for p in itens:
        if p["atual"]:
            continue
        if plano_atual["sem_parametros"]:
            p["explicacao"] = textos.t("explicacao_plano_sem_atual", idioma, risco_abs=p["risco_pct"])
            continue
        risco = p["risco_pct"] - plano_atual["risco_pct"]
        if p["retorno_ano"] is None or plano_atual["retorno_ano"] is None:
            p["explicacao"] = textos.t("explicacao_plano_sem_retorno", idioma, risco=risco)
        else:
            dif = p["retorno_ano"] - plano_atual["retorno_ano"]
            p["explicacao"] = textos.t("explicacao_plano", idioma, risco=risco, retorno=dif, moeda=ctx["moeda"])
    return {"itens": itens, "culturas_ignoradas": ignoradas, "fontes": ctx["fontes"]}
