"""Testes unitarios de web/apresentacao.py (T4: C11..C14)."""

from __future__ import annotations

from pathlib import Path

from core.erros import ErroFonteDados, ErroPontoInvalido
from web.apresentacao import (
    aviso_anos_sem_estacao,
    cards_clima,
    cards_planos,
    cards_ranking,
    dados_grafico,
    marcadores,
    mensagem_erro,
    popup,
    prioridades_vazias,
    selo,
)


def _exemplo_estacao() -> dict:
    return {
        "modo": "estacao",
        "periodos": {
            "1995-2009": {
                "chuva_mm": 1450.0,
                "inicio": "10-12",
                "fim": "04-18",
                "veranicos": 1.4,
                "dias_35c": 3.0,
            },
            "2010-2025": {
                "chuva_mm": 1320.0,
                "inicio": "10-24",
                "fim": "04-12",
                "veranicos": 2.8,
                "dias_35c": 11.0,
            },
        },
        "anos_sem_estacao": 1,
        "chuva_por_ano": [
            {"ano": ano, "chuva_mm": 1300.0 + (ano % 5) * 20}
            for ano in range(1995, 2026)
        ],
    }
def test_cards_clima_cinco_indicadores() -> None:
    """C11 (SITE-11): Modo estacao devolve 5 cards com antes, depois e diferenca."""
    cards, nota = cards_clima(_exemplo_estacao(), idioma="pt")
    assert nota is None
    assert len(cards) == 5
    for card in cards:
        assert card["titulo"]
        assert card["antes"] != "—"
        assert card["depois"] != "—"
        assert card["diferenca"] != "—"
    assert cards[0]["diferenca"] == "-130 mm"
    assert cards[1]["diferenca"] == "+12 d"
    assert cards[2]["diferenca"] == "-6 d"


def test_cards_clima_modo_anual() -> None:
    """C12 (SITE-12): Modo anual devolve 2 cards e a nota explicativa."""
    dados = {
        "modo": "anual",
        "periodos": {
            "1995-2009": {"chuva_mm": 900.0, "dias_35c": 2.0},
            "2010-2025": {"chuva_mm": 950.0, "dias_35c": 5.0},
        },
        "anos_sem_estacao": 25,
    }
    cards, nota = cards_clima(dados, idioma="pt")
    assert len(cards) == 2
    assert nota == "Sem estação chuvosa definida: comparando o ano inteiro"


def test_dados_grafico_chuva_por_ano_periodos() -> None:
    """C13 (SITE-13): DataFrame tem 31 linhas e periodos 1995–2009 / 2010–2025."""
    df = dados_grafico(_exemplo_estacao())
    assert len(df) == 31
    assert list(df.columns) == ["ano", "chuva_mm", "periodo"]
    assert df.loc[df["ano"] == 2009, "periodo"].iloc[0] == "1995–2009"
    assert df.loc[df["ano"] == 2010, "periodo"].iloc[0] == "2010–2025"


def test_aviso_anos_sem_estacao() -> None:
    """C14 (SITE-14): Mostra aviso somente quando anos_sem_estacao > 0."""
    assert (
        aviso_anos_sem_estacao({"anos_sem_estacao": 2}, idioma="pt")
        == "Anos sem estação chuvosa detectada: 2"
    )
    assert aviso_anos_sem_estacao({"anos_sem_estacao": 0}, idioma="pt") is None

def test_cards_ranking_ordem_e_campos() -> None:
    """C17 (SITE-17): Mantem a ordem do motor e preenche todos os campos."""
    dados = {
        "itens": [
            {
                "cultura": "Sorgo",
                "nota": 82.0,
                "risco_pct": 12,
                "anos_quebra": "2/16",
                "nota_solo": 4,
                "retorno": 1850.0,
                "moeda": "BRL",
                "preliminar": False,
                "explicacao": "Tolera veranicos.",
            },
            {
                "cultura": "Soja",
                "nota": 48.0,
                "risco_pct": 44,
                "anos_quebra": "7/16",
                "nota_solo": 4,
                "retorno": 2100.0,
                "moeda": "BRL",
                "preliminar": False,
                "explicacao": "Risco alto de seca.",
            },
        ]
    }
    cards = cards_ranking(dados, idioma="pt")
    assert [c["titulo"] for c in cards] == ["Sorgo", "Soja"]
    assert cards[0]["nota"] == 82.0
    assert cards[0]["risco_txt"] == "Risco de quebra: 12%"
    assert cards[0]["anos_quebra"] == "2/16"
    assert cards[0]["nota_solo"] == 4.0
    assert cards[0]["explicacao"] == "Tolera veranicos."
    assert cards[0]["aviso_preliminar"] is None


def test_retorno_ou_sem_dado() -> None:
    """C18 (SITE-18): Mostra valor com moeda ou 'Retorno: sem dado' quando None."""
    dados = {
        "itens": [
            {
                "cultura": "Milho",
                "nota": 70.0,
                "risco_pct": 20,
                "anos_quebra": "3/16",
                "nota_solo": 3,
                "retorno": 2400.0,
                "moeda": "BRL",
                "preliminar": False,
                "explicacao": "Bom retorno.",
            },
            {
                "cultura": "Feijão",
                "nota": 64.0,
                "risco_pct": 19,
                "anos_quebra": "3/16",
                "nota_solo": 4,
                "retorno": None,
                "moeda": "BRL",
                "preliminar": False,
                "explicacao": "Sem preço municipal.",
            },
        ]
    }
    cards = cards_ranking(dados, idioma="pt")
    assert cards[0]["retorno_txt"] == "Retorno: 2.400 BRL"
    assert cards[1]["retorno_txt"] == "Retorno: sem dado"


def test_card_ranking_preliminar_mostra_aviso() -> None:
    """SITE-41: Card com preliminar=True inclui aviso da FAO no idioma."""
    dados = {
        "itens": [
            {
                "cultura": "Painço",
                "nota": 60.0,
                "risco_pct": 15,
                "anos_quebra": "2/16",
                "nota_solo": 3,
                "retorno": None,
                "moeda": None,
                "preliminar": True,
                "explicacao": "Cultura alternativa.",
            }
        ]
    }
    cards_pt = cards_ranking(dados, idioma="pt")
    cards_en = cards_ranking(dados, idioma="en")
    assert (
        cards_pt[0]["aviso_preliminar"]
        == "parâmetros genéricos da FAO, não calibrados para a região"
    )
    assert (
        cards_en[0]["aviso_preliminar"]
        == "generic FAO parameters, not calibrated for the region"
    )


def test_prioridades_vazias() -> None:
    """C20 (SITE-20): Detecta quando as 3 prioridades estao zeradas."""
    assert prioridades_vazias(0, 0, 0) is True
    assert prioridades_vazias(40, 0, 0) is False

def test_cards_planos_atual_primeiro() -> None:
    """C25 (SITE-25): O plano atual aparece primeiro com rotulo 'Seu plano atual'."""
    dados = {
        "itens": [
            {
                "plano": ["Soja", "Sorgo", "Milho"],
                "nota": 78.0,
                "risco_pct": 14,
                "nota_solo": 4.0,
                "retorno_ano": 1780.0,
                "moeda": "BRL",
                "atual": False,
                "preliminar": False,
                "explicacao": "Alterna leguminosa e graminea.",
            },
            {
                "plano": ["Milho", "Milho", "Milho"],
                "nota": 54.0,
                "risco_pct": 31,
                "nota_solo": 2.0,
                "retorno_ano": 1420.0,
                "moeda": "BRL",
                "atual": True,
                "preliminar": False,
                "explicacao": None,
            },
        ]
    }
    cards = cards_planos(dados, idioma="pt")
    assert cards[0]["atual"] is True
    assert cards[0]["rotulo"] == "Seu plano atual"
    assert cards[0]["culturas"] == ["Milho", "Milho", "Milho"]
    assert cards[1]["atual"] is False
    assert cards[1]["culturas"] == ["Soja", "Sorgo", "Milho"]


def test_cards_planos_campos() -> None:
    """C26 (SITE-26): Cada plano traz nota, risco, solo, retorno/sem dado e explicacao."""
    dados = {
        "itens": [
            {
                "plano": ["Soja", "Milho", "Feijão"],
                "nota": 71.0,
                "risco_pct": 18,
                "nota_solo": 3.5,
                "retorno_ano": None,
                "moeda": "BRL",
                "atual": False,
                "preliminar": True,
                "explicacao": "Bom para o solo; feijão sem preço municipal.",
            }
        ]
    }
    cards = cards_planos(dados, idioma="pt")
    c = cards[0]
    assert c["nota"] == 71.0
    assert c["risco_txt"] == "Risco de quebra: 18%"
    assert c["nota_solo"] == 3.5
    assert c["retorno_txt"] == "Retorno: sem dado"
    assert c["explicacao"] == "Bom para o solo; feijão sem preço municipal."
    assert (
        c["aviso_preliminar"]
        == "parâmetros genéricos da FAO, não calibrados para a região"
    )


def test_selo_niveis_de_precisao() -> None:
    """SITE-05: Traduz municipal, pais e clima nos idiomas."""
    assert selo("municipal", "pt") == "Dados municipais"
    assert selo("pais", "en") == "Country data"
    assert selo("clima", "es") == "Estimado por el clima"


def test_mensagem_erro_motor() -> None:
    """SITE-07/08: Converte ErroPontoInvalido e ErroFonteDados."""
    assert "terra firme" in mensagem_erro(ErroPontoInvalido("mar"), "pt")
    assert "unavailable" in mensagem_erro(ErroFonteDados("timeout"), "en")


def test_marcadores_observacoes() -> None:
    """C32 (SITE-32): Gera um marcador por observacao valida."""
    obs = [
        {"lat": -17.8, "lon": -50.92, "texto": "Folha seca"},
        {"lat": -0.3, "lon": 36.07, "texto": "Solo bom"},
    ]
    res = marcadores(obs)
    assert len(res) == 2
    assert res[0]["lat"] == -17.8
    assert res[0]["lon"] == -50.92
    assert "Folha seca" in res[0]["popup"]


def test_popup_observacao_campos(tmp_path: Path) -> None:
    """C33 (SITE-33): Popup contem data, texto, descricao_ia e miniatura."""
    foto = tmp_path / "campo.png"
    foto.write_bytes(b"\x89PNG\r\n\x1a\n")
    html_popup = popup(
        {
            "data": "2026-11-10",
            "texto": "Milho sentindo seca",
            "descricao_ia": "Estresse hidrico moderado",
            "foto_path": str(foto),
        }
    )
    assert "2026-11-10" in html_popup
    assert "Milho sentindo seca" in html_popup
    assert "Estresse hidrico moderado" in html_popup
    assert "data:image/png;base64," in html_popup
