"""Camada 2 (global): produtividade e preço por país (data/faostat.csv).

Colunas do CSV: iso2, cultura, produtividade_t_ha, preco_usd_t.
"""

from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "data" / "faostat.csv"


def linhas_pais(iso2, path=None):
    """Cultura -> {produtividade_t_ha, preco_usd_t} do país; {} sem linhas ou sem o arquivo."""
    path = Path(path or CSV)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    df = df[df["iso2"] == iso2]
    return {r["cultura"]: {"produtividade_t_ha": float(r["produtividade_t_ha"]), "preco_usd_t": float(r["preco_usd_t"])} for r in df.to_dict("records")}

