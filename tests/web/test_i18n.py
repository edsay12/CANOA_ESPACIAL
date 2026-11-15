from web import i18n


def test_mesmas_chaves_nos_3_idiomas():
    chaves = set(i18n.TEXTOS["pt"])
    assert chaves
    assert set(i18n.TEXTOS["en"]) == chaves
    assert set(i18n.TEXTOS["es"]) == chaves
    for chave in chaves:
        for cod in ("pt", "en", "es"):
            assert isinstance(i18n.TEXTOS[cod][chave], str)
            assert i18n.TEXTOS[cod][chave].strip()


def test_idioma_desconhecido_usa_pt():
    assert i18n.IDIOMAS == {"Português": "pt", "English": "en", "Español": "es"}
    assert i18n.t("abertura", "fr") == i18n.t("abertura", "pt")
    assert i18n.t("risco_quebra", "pt", n=40) == "Risco de quebra: 40%"


def test_texto_limites():
    texto_pt = i18n.t("limites", "pt").lower()
    assert "50 km" in texto_pt
    assert "pragas" in texto_pt and "doenças" in texto_pt
    assert "janela" in texto_pt and "clima" in texto_pt
    assert "irrigação" in texto_pt


def test_textos_localizacao_seguem_os_frames():
    assert i18n.t("titulo_local") == "Onde fica sua terra?"
    assert i18n.t("instrucao_local") == "Toque no mapa, no lugar da sua propriedade."
    assert i18n.t("instrucao_local_mobile") == "Toque no mapa."
    assert i18n.t("dica_mapa") == "Toque em qualquer lugar do mapa"
    assert i18n.t("exemplos_local") == "Ou escolha um lugar pronto"
    assert i18n.t("ver_clima") == "Ver o que mudou no meu clima"
    assert i18n.t("ver_clima_mobile") == "Ver meu clima"
    assert i18n.t("titulo_local", "en") == "Where is your land?"
    assert i18n.t("titulo_local", "es") == "¿Dónde está tu tierra?"
