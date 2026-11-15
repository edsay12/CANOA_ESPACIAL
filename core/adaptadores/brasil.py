"""Camada 3 (Brasil): culturas, produtividade e preço do município mais próximo. Opcional.

Lê `data/brasil_municipal.csv` com as colunas municipio, lat, lon, cultura, produtividade_t_ha, preco_brl_t.
Sem o arquivo, `dados` devolve None e o contexto cai para a camada global.
"""

import math
from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parent.parent.parent / "data" / "brasil_municipal.csv"


def dados(lat, lon, path=None):
    path = Path(path or CSV)
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if df.empty:
        return None
    # shortcut: distância plana com correção de longitude pelo cosseno; basta para achar o município vizinho
    dist = (df["lat"] - lat) ** 2 + ((df["lon"] - lon) * math.cos(math.radians(lat))) ** 2
    mun = df.loc[dist.idxmin(), "municipio"]
    linhas = df[df["municipio"] == mun]
    return {
        "municipio": mun,
        "culturas": linhas["cultura"].tolist(),
        "produtividade": dict(zip(linhas["cultura"], linhas["produtividade_t_ha"].astype(float), strict=True)),
        "preco": dict(zip(linhas["cultura"], linhas["preco_brl_t"].astype(float), strict=True)),
    }
