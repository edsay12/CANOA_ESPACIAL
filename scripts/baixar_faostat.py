"""Gera data/faostat.csv (iso2, cultura, produtividade_t_ha, preco_usd_t) a partir dos bulks do FAOSTAT.

Uso: python -I scripts/baixar_faostat.py DIR_DOWNLOAD
Baixa QCL e PP em DIR_DOWNLOAD/qcl e DIR_DOWNLOAD/pp (se ainda não existirem) e grava data/faostat.csv.
Produtividade: média dos 5 anos mais recentes com dado (FAO "Yield"); preço: idem (FAO "Producer Price (USD/tonne)", anual).
M49 -> ISO2 via data/paises.geojson (mesma fonte de core/pais.py); agregados regionais não têm ISO e caem fora.
"""
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BULK = "https://bulks-faostat.fao.org/production/"
QCL = "Production_Crops_Livestock_E_All_Data_(Normalized)"
PP = "Prices_E_All_Data_(Normalized)"
CULTURAS = {
    "Maize (corn)": "Milho", "Soya beans": "Soja", "Sorghum": "Sorgo granifero", "Wheat": "Trigo",
    "Rice": "Arroz", "Beans, dry": "Feijao comum", "Seed cotton, unginned": "Algodao",
    "Sunflower seed": "Girassol", "Groundnuts, excluding shelled": "Amendoim", "Potatoes": "Batata",
    "Barley": "Cevada", "Rape or colza seed": "Colza/Canola", "Chick peas, dry": "Grao-de-bico",
    "Cow peas, dry": "Feijao-caupi", "Millet": "Milheto",
}
PARA_T_HA = {"kg/ha": 1e-3, "100 g/ha": 1e-4, "hg/ha": 1e-4, "t/ha": 1.0}


def baixar(nome, destino):
    destino.mkdir(parents=True, exist_ok=True)
    zp = destino / f"{nome}.zip"
    if not zp.exists():
        urllib.request.urlretrieve(BULK + urllib.request.quote(f"{nome}.zip"), zp)
    with zipfile.ZipFile(zp) as z, z.open(f"{nome}.csv") as f:
        df = pd.read_csv(f, encoding="latin1", dtype={"Area Code (M49)": str}, low_memory=False)
    return df[df["Item"].isin(CULTURAS)]


def media_5_recentes(df, nome):
    df = df.dropna(subset=["Value"]).sort_values("Year")
    g = df.groupby(["Area Code (M49)", "Item"])
    out = g.tail(5).groupby(["Area Code (M49)", "Item"]).agg(**{nome: ("Value", "mean"), f"anos_{nome}": ("Year", lambda y: f"{y.min()}-{y.max()}")})
    return out


def main(dir_download):
    d = Path(dir_download)
    qcl = baixar(QCL, d / "qcl")
    y = qcl[qcl["Element"] == "Yield"].copy()
    desconhecidas = set(y["Unit"]) - set(PARA_T_HA)
    assert not desconhecidas, f"unidade de Yield inesperada: {desconhecidas}"
    y["Value"] = y["Value"] * y["Unit"].map(PARA_T_HA)

    pp = baixar(PP, d / "pp")
    p = pp[(pp["Element"] == "Producer Price (USD/tonne)") & (pp["Months"] == "Annual value")]

    df = media_5_recentes(y, "produtividade_t_ha").join(media_5_recentes(p, "preco_usd_t"), how="inner").reset_index()

    props = [f["properties"] for f in json.loads((RAIZ / "data" / "paises.geojson").read_text())["features"]]
    m49_iso2 = {p["ISO_N3_EH"]: p["ISO_A2_EH"] for p in props if "-99" not in (str(p["ISO_N3_EH"]), str(p["ISO_A2_EH"]))}
    df["iso2"] = df["Area Code (M49)"].str.lstrip("'").map(m49_iso2)
    df["cultura"] = df["Item"].map(CULTURAS)
    df = df.dropna(subset=["iso2"])
    assert not df.duplicated(["iso2", "cultura"]).any()

    cols = ["iso2", "cultura", "produtividade_t_ha", "preco_usd_t"]
    df.sort_values(["iso2", "cultura"])[cols].round(3).to_csv(RAIZ / "data" / "faostat.csv", index=False)
    print(len(df), "linhas,", df["iso2"].nunique(), "países")
    print("anos produtividade:", df["anos_produtividade_t_ha"].value_counts().head(3).to_dict())
    print("anos preço:", df["anos_preco_usd_t"].value_counts().head(3).to_dict())


if __name__ == "__main__":
    main(sys.argv[1])
