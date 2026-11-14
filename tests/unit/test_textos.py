from core import textos


def test_mesmas_chaves_nos_3_idiomas():
    chaves = set(textos.TEXTOS["pt"])
    assert chaves
    assert set(textos.TEXTOS["en"]) == chaves
    assert set(textos.TEXTOS["es"]) == chaves
    v = {"depois": 9, "n_depois": 15, "antes": 4, "n_antes": 15}
    frases = {i: textos.t("explicacao_safra", i, **v) for i in ("pt", "en", "es")}
    assert len(set(frases.values())) == 3
    assert frases["pt"] == "faltou água em 9 de 15 anos desde 2010; antes eram 4 de 15"


def test_idioma_desconhecido_usa_en():
    v = {"depois": 9, "n_depois": 15, "antes": 4, "n_antes": 15}
    assert textos.t("explicacao_safra", "fr", **v) == textos.t("explicacao_safra", "en", **v)
    assert "water" in textos.t("explicacao_safra", "fr", **v)
