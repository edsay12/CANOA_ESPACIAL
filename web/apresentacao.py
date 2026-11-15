"""Transforma os resultados do motor em dados prontos para exibicao no site."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from web.i18n import t

_LIMITE_PERIODO_ANTERIOR = 2009


def _fmt_num(valor: float | None, casas: int = 0, sufixo: str = "") -> str:
    if valor is None:
        return "—"
    if casas == 0:
        texto = f"{round(float(valor)):,}".replace(",", ".")
    else:
        texto = f"{float(valor):.{casas}f}".replace(".", ",")
    return f"{texto}{sufixo}"


def _fmt_mmdd(mmdd: str | None) -> str:
    if not mmdd:
        return "—"
    partes = mmdd.split("-")
    if len(partes) != 2:
        return mmdd
    return f"{partes[1]}/{partes[0]}"


def _diff_num(
    antes: float | None,
    depois: float | None,
    casas: int = 0,
    sufixo: str = "",
) -> str:
    if antes is None or depois is None:
        return "—"
    dif = float(depois) - float(antes)
    sinal = "+" if dif > 0 else ""
    if casas == 0:
        corpo = f"{round(dif):,}".replace(",", ".")
    else:
        corpo = f"{dif:.{casas}f}".replace(".", ",")
    return f"{sinal}{corpo}{sufixo}"


def _diff_dias_mmdd(antes: str | None, depois: str | None) -> str:
    if not antes or not depois:
        return "—"
    m1, d1 = (int(x) for x in antes.split("-"))
    m2, d2 = (int(x) for x in depois.split("-"))
    dt1 = date(2001, m1, d1)
    dt2 = date(2001, m2, d2)
    dias = (dt2 - dt1).days
    if dias > 180:
        dias -= 365
    elif dias < -180:
        dias += 365
    sinal = "+" if dias > 0 else ""
    return f"{sinal}{dias} d"


def cards_clima(
    resultado: dict[str, Any], idioma: str = "pt"
) -> tuple[list[dict[str, str]], str | None]:
    """Monta os cartoes de mudanca climatica e uma nota opcional para o modo anual."""
    modo = resultado.get("modo", "estacao")
    periodos = resultado.get("periodos", {})
    antes = periodos.get("1995-2009", {})
    depois = periodos.get("2010-2025", {})

    if modo == "anual":
        cards = [
            {
                "titulo": t("ind_chuva_anual", idioma),
                "antes": _fmt_num(antes.get("chuva_mm"), 0, " mm"),
                "depois": _fmt_num(depois.get("chuva_mm"), 0, " mm"),
                "diferenca": _diff_num(
                    antes.get("chuva_mm"), depois.get("chuva_mm"), 0, " mm"
                ),
            },
            {
                "titulo": t("ind_calor", idioma),
                "antes": _fmt_num(antes.get("dias_35c"), 1),
                "depois": _fmt_num(depois.get("dias_35c"), 1),
                "diferenca": _diff_num(
                    antes.get("dias_35c"), depois.get("dias_35c"), 1
                ),
            },
        ]
        return cards, t("nota_anual", idioma)

    cards = [
        {
            "titulo": t("ind_chuva", idioma),
            "antes": _fmt_num(antes.get("chuva_mm"), 0, " mm"),
            "depois": _fmt_num(depois.get("chuva_mm"), 0, " mm"),
            "diferenca": _diff_num(
                antes.get("chuva_mm"), depois.get("chuva_mm"), 0, " mm"
            ),
        },
        {
            "titulo": t("ind_inicio", idioma),
            "antes": _fmt_mmdd(antes.get("inicio")),
            "depois": _fmt_mmdd(depois.get("inicio")),
            "diferenca": _diff_dias_mmdd(
                antes.get("inicio"), depois.get("inicio")
            ),
        },
        {
            "titulo": t("ind_fim", idioma),
            "antes": _fmt_mmdd(antes.get("fim")),
            "depois": _fmt_mmdd(depois.get("fim")),
            "diferenca": _diff_dias_mmdd(
                antes.get("fim"), depois.get("fim")
            ),
        },
        {
            "titulo": t("ind_veranicos", idioma),
            "antes": _fmt_num(antes.get("veranicos"), 1),
            "depois": _fmt_num(depois.get("veranicos"), 1),
            "diferenca": _diff_num(
                antes.get("veranicos"), depois.get("veranicos"), 1
            ),
        },
        {
            "titulo": t("ind_calor", idioma),
            "antes": _fmt_num(antes.get("dias_35c"), 1),
            "depois": _fmt_num(depois.get("dias_35c"), 1),
            "diferenca": _diff_num(
                antes.get("dias_35c"), depois.get("dias_35c"), 1
            ),
        },
    ]
    return cards, None


def dados_grafico(resultado: dict[str, Any]) -> pd.DataFrame:
    """Converte chuva_por_ano em DataFrame com colunas ano, chuva_mm e periodo."""
    linhas = []
    for item in resultado.get("chuva_por_ano", []):
        ano = int(item["ano"])
        periodo = (
            "1995–2009" if ano <= _LIMITE_PERIODO_ANTERIOR else "2010–2025"
        )
        linhas.append(
            {
                "ano": ano,
                "chuva_mm": float(item["chuva_mm"]),
                "periodo": periodo,
            }
        )
    return pd.DataFrame(linhas, columns=["ano", "chuva_mm", "periodo"])


def aviso_anos_sem_estacao(
    resultado: dict[str, Any], idioma: str = "pt"
) -> str | None:
    """Retorna aviso formatado quando houver anos sem estacao chuvosa detectada."""
    n = int(resultado.get("anos_sem_estacao", 0) or 0)
    if n <= 0:
        return None
    return t("anos_sem_estacao", idioma, n=n)

def _fmt_retorno(
    valor: float | None, moeda: str | None, idioma: str
) -> str:
    if valor is None:
        return t("retorno_sem_dado", idioma)
    valor_fmt = _fmt_num(valor, 0)
    return t(
        "retorno_com_moeda",
        idioma,
        valor=valor_fmt,
        moeda=moeda or "",
    ).strip()


def cards_ranking(
    resultado: dict[str, Any], idioma: str = "pt"
) -> list[dict[str, Any]]:
    """Formata os itens do ranking preservando a ordem retornada pelo motor."""
    cards: list[dict[str, Any]] = []
    for item in resultado.get("itens", []):
        nota_solo = item.get("nota_solo")
        cards.append(
            {
                "titulo": str(item.get("cultura", "")),
                "nota": float(item.get("nota", 0.0)),
                "risco_txt": t(
                    "risco_quebra",
                    idioma,
                    n=round(float(item.get("risco_pct", 0))),
                ),
                "anos_quebra": str(item.get("anos_quebra", "")),
                "nota_solo": (
                    float(nota_solo) if nota_solo is not None else None
                ),
                "retorno_txt": _fmt_retorno(
                    item.get("retorno"), item.get("moeda"), idioma
                ),
                "explicacao": str(item.get("explicacao", "")),
                "aviso_preliminar": (
                    t("aviso_preliminar", idioma)
                    if item.get("preliminar")
                    else None
                ),
            }
        )
    return cards


def prioridades_vazias(
    retorno: float, seguranca: float, solo: float
) -> bool:
    """Retorna True quando todas as prioridades estao zeradas (SITE-20)."""
    return float(retorno) <= 0 and float(seguranca) <= 0 and float(solo) <= 0

def cards_planos(
    resultado: dict[str, Any], idioma: str = "pt"
) -> list[dict[str, Any]]:
    """Formata os planos de rotacao colocando o plano atual primeiro (SITE-25)."""
    itens = list(resultado.get("itens", []))
    ordenados = [p for p in itens if p.get("atual")] + [
        p for p in itens if not p.get("atual")
    ]
    cards: list[dict[str, Any]] = []
    for idx, item in enumerate(ordenados, start=1):
        atual = bool(item.get("atual"))
        risco = item.get("risco_pct")
        risco_txt = (
            "—"
            if risco is None
            else t("risco_quebra", idioma, n=round(float(risco)))
        )
        nota = item.get("nota")
        nota_solo = item.get("nota_solo")
        cards.append(
            {
                "rotulo": (
                    t("plano_atual", idioma) if atual else f"#{idx}"
                ),
                "atual": atual,
                "culturas": [str(c) for c in item.get("plano", [])],
                "nota": float(nota) if nota is not None else None,
                "risco_txt": risco_txt,
                "nota_solo": (
                    float(nota_solo) if nota_solo is not None else None
                ),
                "retorno_txt": _fmt_retorno(
                    item.get("retorno_ano"), item.get("moeda"), idioma
                ),
                "explicacao": (
                    str(item["explicacao"])
                    if item.get("explicacao")
                    else None
                ),
                "aviso_preliminar": (
                    t("aviso_preliminar", idioma)
                    if item.get("preliminar")
                    else None
                ),
            }
        )
    return cards