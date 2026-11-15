from bot_logica import idioma


def test_language_code_para_idioma():
    for codigo, esperado in [
        ("pt", "pt"), ("pt-BR", "pt"), ("pt-PT", "pt"),
        ("en", "en"), ("en-US", "en"),
        ("es", "es"), ("es-419", "es"), ("ES", "es"),
        ("fr", "en"), ("sw", "en"), ("de-DE", "en"), ("", "en"), (None, "en"), ("p", "en"),
    ]:
        assert idioma.idioma(codigo) == esperado, codigo


def test_textos_nos_3_idiomas():
    chaves = set(idioma.TEXTOS["pt"])
    assert set(idioma.TEXTOS["en"]) == chaves == set(idioma.TEXTOS["es"])
    # textos exatos da spec (BOT-24, BOT-25, foto AC 5, áudio AC 2, edge 2)
    assert idioma.t("limite", "pt") == "Você atingiu o limite de 20 mensagens por hora. Tente de novo mais tarde."
    assert idioma.t("llm_indisponivel", "pt") == "O assistente está indisponível agora. Tente de novo em alguns minutos."
    assert idioma.t("confirme_campo", "pt") == "Confirme no campo: pode ser falta d'água, praga, doença ou compactação."
    assert idioma.t("ponto_invalido", "pt") == "Esse ponto fica fora de terra firme. Mande outra localização."
    assert "até o fim do evento" in idioma.t("boas_vindas", "pt")
    assert idioma.t("limite", "fr") == idioma.t("limite", "en")
