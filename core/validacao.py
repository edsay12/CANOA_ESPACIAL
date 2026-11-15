"""Validação das entradas comuns do motor."""

import math
import re
from datetime import date

PESOS_PADRAO = {"retorno": 0.4, "seguranca": 0.4, "solo": 0.2}


def ponto(lat, lon):
    if not -90 <= lat <= 90:
        raise ValueError(f"lat fora de [-90, 90]: {lat}")
    if not -180 <= lon <= 180:
        raise ValueError(f"lon fora de [-180, 180]: {lon}")


def data_mmdd(s):
    """'MM-DD' -> (mes, dia). 02-29 é recusado porque a semeadura se repete em anos não bissextos."""
    if not isinstance(s, str) or not re.fullmatch(r"\d{2}-\d{2}", s):
        raise ValueError(f"data_semeadura não é MM-DD: {s!r}")
    mes, dia = int(s[:2]), int(s[3:])
    try:
        date(2001, mes, dia)
    except ValueError:
        raise ValueError(f"data_semeadura inválida: {s!r}") from None
    return mes, dia


def pesos(prioridades=None):
    """Pesos de retorno, segurança e solo reescalados para somar 1; ausentes valem 0."""
    if prioridades is None:
        return dict(PESOS_PADRAO)
    extras = set(prioridades) - set(PESOS_PADRAO)
    if extras:
        raise ValueError(f"prioridades desconhecidas: {sorted(extras)}")
    p = {k: float(prioridades.get(k, 0)) for k in PESOS_PADRAO}
    if not all(math.isfinite(v) for v in p.values()):
        raise ValueError("prioridades precisam ser números finitos")
    if any(v < 0 for v in p.values()):
        raise ValueError("prioridades não podem ser negativas")
    total = sum(p.values())
    if total == 0:
        raise ValueError("ao menos uma prioridade deve ser maior que 0")
    return {k: v / total for k, v in p.items()}
