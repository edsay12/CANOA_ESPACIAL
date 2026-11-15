"""Parâmetros das culturas (data/culturas.csv)."""

from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "data" / "culturas.csv"
CAMPOS_MODELO = ("dias_ini", "dias_des", "dias_mid", "dias_fim", "kc_ini", "kc_mid", "kc_fim", "raiz_m", "p_deplecao", "ky")


def carregar(path=None):
    """Nome da cultura -> dict da linha; célula vazia vira None."""
    df = pd.read_csv(path or CSV)
    df = df.astype(object).where(df.notna(), None)
    return {r["cultura"]: r for r in df.to_dict("records")}


def preliminar(c):
    """MOT-63: parâmetro não validado pela equipe (validado ausente ou diferente de true)."""
    return str(c.get("validado")).lower() != "true"


def completa(c):
    return all(c.get(k) is not None for k in CAMPOS_MODELO)
