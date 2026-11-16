"""Testes de integracao das abas de app.py com Streamlit AppTest."""

from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from core.erros import ErroFonteDados

APP_PATH = str(Path(__file__).resolve().parents[2] / "app.py")


@pytest.fixture(autouse=True)
def _mock_folium(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("streamlit_folium.st_folium", lambda *_, **__: {})


class _ServicoFake:
    def __init__(
        self,
        ctx: dict[str, Any] | Exception | None = None,
        clima_res: dict[str, Any] | Exception | None = None,
        ranking_res: dict[str, Any] | Exception | None = None,
        planos_res: dict[str, Any] | Exception | None = None,
        db_ativo: bool = False,
        observacoes_lista: list[dict[str, Any]] | None = None,
    ) -> None:
        self._ctx = ctx or {
            "pais": {"codigo": "BR", "nome": "Brasil"},
            "nivel_precisao": "municipal",
            "culturas": ["soja", "milho", "sorgo"],
            "fontes": ["NASA POWER", "MapBiomas"],
        }
        self._clima_res = clima_res or {
            "modo": "estacao",
            "resumo": "A estacao chuvosa encurtou 12 dias.",
            "periodos": {
                "1995-2009": {
                    "chuva_mm": 1200,
                    "inicio": "10-05",
                    "fim": "04-15",
                    "veranicos": 1.2,
                    "dias_35c": 8.0,
                },
                "2010-2025": {
                    "chuva_mm": 1050,
                    "inicio": "10-18",
                    "fim": "04-10",
                    "veranicos": 2.1,
                    "dias_35c": 14.5,
                },
            },
            "chuva_por_ano": [
                {"ano": 1995, "chuva_mm": 1210},
                {"ano": 2024, "chuva_mm": 1030},
            ],
            "anos_sem_estacao": 2,
            "fontes": ["NASA POWER"],
        }
        self._ranking_res = (
            ranking_res
            if ranking_res is not None
            else {
                "itens": [
                    {
                        "cultura": "sorgo",
                        "nota": 86.0,
                        "risco_pct": 12.0,
                        "anos_quebra": "2 de 16",
                        "nota_solo": 80.0,
                        "retorno": 3200.0,
                        "moeda": "BRL/ha",
                        "explicacao": "Tolera veranicos longos.",
                        "preliminar": False,
                    },
                    {
                        "cultura": "soja",
                        "nota": 72.0,
                        "risco_pct": 28.0,
                        "anos_quebra": "4 de 16",
                        "nota_solo": 65.0,
                        "retorno": None,
                        "moeda": None,
                        "explicacao": "Sensivel a veranico no florescimento.",
                        "preliminar": True,
                    },
                ],
                "culturas_ignoradas": ["trigo"],
                "fontes": ["NASA POWER", "FAO"],
            }
        )
        self._planos_res = (
            planos_res
            if planos_res is not None
            else {
                "itens": [
                    {
                        "atual": False,
                        "plano": ["soja", "sorgo", "milho"],
                        "nota": 88.0,
                        "risco_pct": 14.0,
                        "nota_solo": 85.0,
                        "retorno_ano": 3500.0,
                        "moeda": "BRL/ha",
                        "explicacao": "Diversifica gramineas e leguminosa.",
                        "preliminar": False,
                    },
                    {
                        "atual": True,
                        "plano": ["soja", "soja", "milho"],
                        "nota": 64.0,
                        "risco_pct": 31.0,
                        "nota_solo": 52.0,
                        "retorno_ano": 2900.0,
                        "moeda": "BRL/ha",
                        "explicacao": "Repeticao de soja reduz saude do solo.",
                        "preliminar": False,
                    },
                ],
                "fontes": ["NASA POWER", "FAO"],
            }
        )
        self.chamadas_ranking: list[dict[str, Any]] = []
        self.chamadas_planos: list[dict[str, Any]] = []
        self.db_ativo = db_ativo
        self._observacoes = observacoes_lista or []
        self.chamadas_observacoes = 0
        self.chamadas_fazenda: list[tuple[float, float]] = []
        self._fazendas: dict[tuple[float, float], int] = {}

    def contexto(self, lat: float, lon: float) -> dict[str, Any]:
        if isinstance(self._ctx, Exception):
            raise self._ctx
        return self._ctx

    def clima(
        self, lat: float, lon: float, idioma: str = "pt"
    ) -> dict[str, Any]:
        if isinstance(self._clima_res, Exception):
            raise self._clima_res
        return self._clima_res

    def ranking(
        self,
        lat: float,
        lon: float,
        data_semeadura: str,
        prioridades: dict[str, float] | None = None,
        idioma: str = "pt",
    ) -> dict[str, Any]:
        self.chamadas_ranking.append(
            {
                "lat": lat,
                "lon": lon,
                "data_semeadura": data_semeadura,
                "prioridades": dict(prioridades or {}),
                "idioma": idioma,
            }
        )
        if isinstance(self._ranking_res, Exception):
            raise self._ranking_res
        return self._ranking_res

    def planos(
        self,
        lat: float,
        lon: float,
        historico: list[str],
        prioridades: dict[str, float] | None = None,
        idioma: str = "pt",
    ) -> dict[str, Any]:
        self.chamadas_planos.append(
            {
                "lat": lat,
                "lon": lon,
                "historico": list(historico),
                "prioridades": dict(prioridades or {}),
                "idioma": idioma,
            }
        )
        if isinstance(self._planos_res, Exception):
            raise self._planos_res
        return self._planos_res

    def db_disponivel(self) -> bool:
        return self.db_ativo

    def observacoes(self) -> list[dict[str, Any]]:
        self.chamadas_observacoes += 1
        return list(self._observacoes)

    def fazenda(self, lat: float, lon: float) -> int:
        chave = (round(float(lat), 2), round(float(lon), 2))
        self.chamadas_fazenda.append(chave)
        if chave not in self._fazendas:
            self._fazendas[chave] = 42
        return self._fazendas[chave]


def test_aba_clima_resumo_cards_e_aviso() -> None:
    """C10, C14: aba 'Seu clima mudou' exibe resumo, 5 metricas e aviso de anos sem estacao."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = _ServicoFake()
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    subheaders = [s.value for s in at.subheader]
    assert "A estacao chuvosa encurtou 12 dias." in subheaders
    assert len(at.metric) == 5
    avisos = [i.value for i in at.info]
    assert any("2" in a for a in avisos)


def test_erro_na_aba_clima_nao_derruba_outras_abas() -> None:
    """C40: erro em servico.clima mostra alerta na aba sem derrubar as demais."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = _ServicoFake(
        clima_res=ErroFonteDados("NASA indisponivel")
    )
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    erros = [e.value for e in at.error]
    assert any("indisponíveis" in e for e in erros)
    assert len(at.tabs) == 3


def test_plantar_controles_padrao() -> None:
    """C15 (SITE-15): data padrao 03-01 e sliders Retorno 40, Seguranca 40, Solo 20."""
    servico = _ServicoFake()
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    assert at.text_input(key="data_semeadura").value == "03-01"
    assert at.slider(key="prio_retorno").value == 40
    assert at.slider(key="prio_seguranca").value == 40
    assert at.slider(key="prio_solo").value == 20
    assert servico.chamadas_ranking[-1]["data_semeadura"] == "03-01"
    assert servico.chamadas_ranking[-1]["prioridades"] == {
        "retorno": 40.0,
        "seguranca": 40.0,
        "solo": 20.0,
    }


def test_plantar_recalcula_ao_mudar() -> None:
    """C16 (SITE-16): mudar a data ou um slider chama ranking com os novos valores."""
    servico = _ServicoFake()
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    at.text_input(key="data_semeadura").set_value("10-15")
    at.slider(key="prio_retorno").set_value(70).run(timeout=15)

    assert servico.chamadas_ranking[-1]["data_semeadura"] == "10-15"
    assert servico.chamadas_ranking[-1]["prioridades"] == {
        "retorno": 70.0,
        "seguranca": 40.0,
        "solo": 20.0,
    }


def test_culturas_ignoradas_listadas() -> None:
    """C19 (SITE-19): culturas_ignoradas nao vazia aparece em 'Culturas sem dados suficientes'."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = _ServicoFake()
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    textos_md = " ".join(m.value for m in at.markdown)
    assert "Culturas sem dados suficientes" in textos_md
    assert "trigo" in textos_md


def test_prioridades_zeradas_nao_chama_motor() -> None:
    """C20 (SITE-20): com os 3 sliders em 0 mostra aviso e nao chama o motor."""
    servico = _ServicoFake()
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    servico.chamadas_ranking.clear()
    at.slider(key="prio_retorno").set_value(0)
    at.slider(key="prio_seguranca").set_value(0)
    at.slider(key="prio_solo").set_value(0).run(timeout=15)

    assert servico.chamadas_ranking == []
    avisos = [w.value for w in at.warning]
    assert "Escolha pelo menos uma prioridade" in avisos


def test_ranking_vazio_mensagem() -> None:
    """C21 (SITE-21): itens vazio mostra 'Nenhuma cultura com dados suficientes para este lugar'."""
    servico = _ServicoFake(
        ranking_res={"itens": [], "culturas_ignoradas": [], "fontes": []}
    )
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    infos = [i.value for i in at.info]
    assert "Nenhuma cultura com dados suficientes para este lugar" in infos


def test_valueerror_mostra_mensagem_no_controle() -> None:
    """C39 (SITE-39): ValueError do motor aparece junto ao controle."""
    servico = _ServicoFake(ranking_res=ValueError("Data de semeadura invalida"))
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    erros = [e.value for e in at.error]
    assert "Data de semeadura invalida" in erros


def test_planos_seletores_candidatas() -> None:
    """C22 (SITE-22): seletores Safra 1, Safra 2, Safra 3 com as culturas candidatas do ponto."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = _ServicoFake()
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    for chave in ("safra_1", "safra_2", "safra_3"):
        seletor = at.selectbox(key=chave)
        assert seletor.options == ["", "soja", "milho", "sorgo"]


def test_planos_historico_incompleto() -> None:
    """C23 (SITE-23): com algum seletor vazio mostra pedido de historico e nao chama o motor."""
    servico = _ServicoFake()
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    at.selectbox(key="safra_1").select("soja")
    at.selectbox(key="safra_2").select("milho").run(timeout=15)

    assert servico.chamadas_planos == []
    infos = [i.value for i in at.info]
    assert "Informe o que você plantou nas últimas 3 safras" in infos


def test_planos_chama_motor_com_historico() -> None:
    """C24, C25 (SITE-24, SITE-25): com 3 safras chama planos e mostra o plano atual primeiro."""
    servico = _ServicoFake()
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    at.selectbox(key="safra_1").select("soja")
    at.selectbox(key="safra_2").select("soja")
    at.selectbox(key="safra_3").select("milho").run(timeout=15)

    assert servico.chamadas_planos[-1]["historico"] == ["soja", "soja", "milho"]
    assert servico.chamadas_planos[-1]["prioridades"] == {
        "retorno": 40.0,
        "seguranca": 40.0,
        "solo": 20.0,
    }
    titulos_planos = [
        s.value for s in at.subheader if "→" in s.value
    ]
    assert titulos_planos[0].startswith("Seu plano atual:")


def test_confiar_lista_fontes() -> None:
    """C29 (SITE-29): painel 'Por que confiar' lista todas as fontes do motor."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = _ServicoFake()
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    assert len(at.expander) == 1
    assert at.expander[0].label == "Por que confiar"
    textos_md = " ".join(m.value for m in at.markdown)
    assert "NASA POWER" in textos_md
    assert "MapBiomas" in textos_md


def test_confiar_link_power() -> None:
    """C31 (SITE-31): 'NASA POWER' no painel aponta para https://power.larc.nasa.gov/."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = _ServicoFake()
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    textos_md = " ".join(m.value for m in at.markdown)
    assert "https://power.larc.nasa.gov/" in textos_md


def test_atualizar_fotos_recarrega() -> None:
    """C34 (SITE-34): clicar em 'Atualizar fotos' recarrega as observacoes do banco."""
    servico = _ServicoFake(
        db_ativo=True,
        observacoes_lista=[
            {
                "lat": -17.79,
                "lon": -50.92,
                "data": "2026-03-10",
                "texto": "Solo umido",
                "descricao_ia": "Cobertura boa",
            }
        ],
    )
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.run(timeout=15)

    assert servico.chamadas_observacoes == 1
    at.button(key="btn_atualizar_fotos").click().run(timeout=15)
    assert servico.chamadas_observacoes == 2


def test_telegram_cria_fazenda_e_link() -> None:
    """C35 (SITE-35): clicar em 'Receber alertas no Telegram' cria fazenda e exibe link."""
    servico = _ServicoFake(db_ativo=True)
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    at.button(key="btn_telegram").click().run(timeout=15)
    assert servico.chamadas_fazenda == [(-17.79, -50.92)]
    textos_md = " ".join(m.value for m in at.markdown)
    assert "https://t.me/" in textos_md
    assert "?start=42" in textos_md


def test_sem_db_esconde_fotos_e_telegram() -> None:
    """SITE-32..35: sem db_disponivel, botoes de fotos e Telegram ficam ocultos."""
    servico = _ServicoFake(db_ativo=False)
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["servico"] = servico
    at.session_state["ponto"] = (-17.79, -50.92)
    at.run(timeout=15)

    chaves_botoes = [b.key for b in at.button]
    assert "btn_atualizar_fotos" not in chaves_botoes
    assert "btn_telegram" not in chaves_botoes


