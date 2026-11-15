"""Escolhe a melhor fonte disponível por ponto: adaptador nacional -> FAOSTAT -> clima.

Contrato: contexto(lat, lon) -> {pais, culturas, fontes, nivel_precisao, classe_climatica, produtividade, moeda}
`produtividade` é cultura -> {produtividade_t_ha, preco_t} na `moeda` do nível usado ({} e None no nível clima).
"""

from core import culturas, global_ctx, pais, power, solo
from core.adaptadores import brasil
from core.erros import ErroPontoInvalido


def classe_climatica(serie):
    anual = serie.assign(chuva=serie["chuva"].fillna(0)).groupby(serie["data"].dt.year)["chuva"].sum().mean()
    if anual < 500:
        return "arido"
    tmedia = (serie["tmax"] + serie["tmin"]) / 2
    mais_frio = tmedia.groupby(serie["data"].dt.month).mean().min()
    if mais_frio >= 18:
        return "tropical"
    return "subtropical" if mais_frio >= 0 else "temperado"


def contexto(lat, lon):
    p = pais.de(lat, lon)
    if p["iso2"] is None:
        raise ErroPontoInvalido("ponto fora de terra")
    classe = classe_climatica(power.serie(lat, lon))
    fontes = ["NASA POWER", solo.agua_disponivel(lat, lon)["fonte"]]
    todas = culturas.carregar()

    br = brasil.dados(lat, lon) if p["iso2"] == "BR" else None
    if br:
        nomes = [c for c in br["culturas"] if c in todas]
        prod = {c: {"produtividade_t_ha": br["produtividade"][c], "preco_t": br["preco"][c]} for c in nomes}
        nivel, moeda = "municipal", "BRL"
        fontes.append("Brasil municipal")
    elif linhas := global_ctx.linhas_pais(p["iso2"]):
        nomes = [c for c in linhas if c in todas]
        prod = {c: {"produtividade_t_ha": linhas[c]["produtividade_t_ha"], "preco_t": linhas[c]["preco_usd_t"]} for c in nomes}
        nivel, moeda = "pais", "USD"
        fontes.append("FAOSTAT")
    else:
        nomes = [n for n, c in todas.items() if classe in str(c.get("climas") or "").split(";")]
        prod, nivel, moeda = {}, "clima", None
    return {
        "pais": p,
        "culturas": nomes,
        "fontes": fontes,
        "nivel_precisao": nivel,
        "classe_climatica": classe,
        "produtividade": prod,
        "moeda": moeda,
    }
