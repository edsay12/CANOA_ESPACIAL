"""Transforma os resultados do motor em dados prontos para exibicao no site."""

from __future__ import annotations

import base64
import html
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from core.erros import ErroFonteDados, ErroPontoInvalido
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


_SELOS = {
    "municipal": "selo_municipal",
    "pais": "selo_pais",
    "clima": "selo_clima",
}


def selo(nivel: str | None, idioma: str = "pt") -> str:
    """Traduz o nivel de precisao retornado por contexto() (SITE-05)."""
    chave = _SELOS.get(str(nivel or ""), "selo_clima")
    return t(chave, idioma)


def mensagem_erro(exc: Exception, idioma: str = "pt") -> str:
    """Converte excecoes do motor em mensagens amigaveis (SITE-07, SITE-08)."""
    if isinstance(exc, ErroPontoInvalido):
        return t("erro_ponto", idioma)
    if isinstance(exc, ErroFonteDados):
        return t("erro_fonte", idioma)
    return str(exc)


def _miniatura_html(caminho: str | None) -> str:
    if not caminho:
        return ""
    arquivo = Path(str(caminho))
    if not arquivo.is_file():
        return ""
    ext = arquivo.suffix.lower().lstrip(".") or "jpeg"
    if ext == "jpg":
        ext = "jpeg"
    dados_b64 = base64.b64encode(arquivo.read_bytes()).decode("ascii")
    return (
        f'<img src="data:image/{ext};base64,{dados_b64}" '
        'style="max-width:180px;max-height:140px;border-radius:6px;margin-top:6px;" />'
    )


def popup(obs: dict[str, Any]) -> str:
    """Monta o HTML do popup da observacao com data, texto, descricao_ia e foto."""
    data_obs = html.escape(str(obs.get("data") or obs.get("criado_em") or ""))
    texto = html.escape(str(obs.get("texto") or ""))
    desc_ia = html.escape(str(obs.get("descricao_ia") or ""))
    foto = _miniatura_html(obs.get("foto_path") or obs.get("foto"))
    partes = [
        f"<strong>{data_obs}</strong>" if data_obs else "",
        f"<p style='margin:4px 0'>{texto}</p>" if texto else "",
        f"<p style='margin:4px 0;color:#555'>{desc_ia}</p>" if desc_ia else "",
        foto,
    ]
    return "".join(p for p in partes if p)


def marcadores(observacoes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prepara os marcadores de observacoes de campo para o mapa (SITE-32)."""
    saida: list[dict[str, Any]] = []
    for obs in observacoes:
        if obs.get("lat") is None or obs.get("lon") is None:
            continue
        saida.append(
            {
                "lat": float(obs["lat"]),
                "lon": float(obs["lon"]),
                "popup": popup(obs),
            }
        )
    return saida
