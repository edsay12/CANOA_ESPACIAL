from datetime import date
from types import SimpleNamespace

import pytest

from bot_logica.conversa import Conversa, dividir
from bot_logica.idioma import t
from bot_logica.limite import Limite
from bot_logica.llm import LLMIndisponivel
from core import db
from core.erros import ErroPontoInvalido


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "db.sqlite"))
    chamadas = []
    motor = SimpleNamespace(
        contexto=lambda lat, lon: {"pais": {"iso2": "BR"}},
        clima_mudou=lambda lat, lon, idioma: {
            "resumo": f"clima {idioma}",
            "fontes": ["NASA POWER"],
        },
        ranking_safra=lambda lat, lon, data_semeadura, idioma: (
            chamadas.append((lat, lon, data_semeadura, idioma))
            or {
                "itens": [
                    {"cultura": "Soja", "risco_pct": 12},
                    {"cultura": "Milho", "risco_pct": 30},
                ]
            }
        ),
    )
    assistente = SimpleNamespace(responder=lambda *args: "Resposta do assistente")
    alertas = SimpleNamespace(verificar=lambda *args, **kwargs: [])
    conversa = Conversa(
        db,
        motor,
        assistente,
        Limite(maximo=100),
        alertas,
        hoje=lambda: date(2026, 11, 15),
    )
    return conversa, motor, assistente, alertas, chamadas


def test_start_boas_vindas_privacidade(ambiente):
    conversa, *_ = ambiente
    resposta = conversa.start(1, [], "pt")
    assert resposta == [t("boas_vindas", "pt")]
    assert "localização" in resposta[0] and "fim do evento" in resposta[0]


def test_start_id_vincula_fazenda(ambiente):
    conversa, *_ = ambiente
    identificador = db.criar_fazenda(-12, -45, "BR")
    assert conversa.start(1, [str(identificador)], "es") == ["clima es"]
    assert db.fazenda_por_chat(1)["id"] == identificador


def test_start_id_inexistente(ambiente):
    conversa, *_ = ambiente
    identificador = db.criar_fazenda(-12, -45, "BR", 1)
    for invalido in ("9999", "xyz", "9" * 100):
        assert conversa.start(1, [invalido], "pt") == [
            t("fazenda_nao_encontrada", "pt")
        ]
        assert db.fazenda_por_chat(1)["id"] == identificador


def test_localizacao_resumo_e_melhor_cultura(ambiente):
    conversa, _, _, _, chamadas = ambiente
    resposta = conversa.localizacao(1, -12, -45, "pt")
    fazenda = db.fazenda_por_chat(1)
    assert (fazenda["lat"], fazenda["lon"], fazenda["pais"]) == (-12, -45, "BR")
    assert "clima pt" in resposta[0] and "Soja" in resposta[0] and "12" in resposta[0]
    assert t("dados_fonte", "pt") in resposta[0]
    assert chamadas == [(-12, -45, "11-15", "pt")]
    conversa.localizacao(1, -13, -46, "en")
    atual = db.fazenda_por_chat(1)
    assert atual["id"] == fazenda["id"] and (atual["lat"], atual["lon"]) == (-13, -46)


def test_pergunta_sem_fazenda_pede_localizacao(ambiente):
    conversa, _, assistente, *_ = ambiente
    chamadas = []
    assistente.responder = lambda *args: chamadas.append(args)
    assert conversa.texto(1, "Qual cultura?", "en") == [t("pedir_localizacao", "en")]
    assert chamadas == []
    db.criar_fazenda(1, 2, "BR", 1)
    assistente.responder = lambda *args: (
        chamadas.append(args) or "Resposta do assistente"
    )
    assert conversa.texto(1, "Qual cultura?", "en") == ["Resposta do assistente"]
    assert chamadas[-1][0:2] == (1, "Qual cultura?")
    assert chamadas[-1][2]["chat_id"] == "1" and chamadas[-1][3] == "en"
    assistente.responder = lambda *args: (_ for _ in ()).throw(
        LLMIndisponivel("secret")
    )
    assert conversa.texto(1, "Qual cultura?", "en") == [t("llm_indisponivel", "en")]


def test_alerta_inscreve(ambiente):
    conversa, *_ = ambiente
    fazenda = db.criar_fazenda(1, 2, "BR", 1)
    resposta = conversa.alerta(1, ["SORGO", "GRANIFERO", "15/02/2026"], "es")
    alerta = db.listar_alertas()[0]
    assert (
        alerta["fazenda_id"],
        alerta["cultura"],
        alerta["data_plantio"],
        alerta["idioma"],
    ) == (fazenda, "Sorgo granifero", "2026-02-15", "es")
    assert resposta == [
        t("alerta_ok", "es", cultura="Sorgo granifero", data="15/02/2026")
    ]


def test_alerta_entrada_invalida(ambiente):
    conversa, *_ = ambiente
    db.criar_fazenda(1, 2, "BR", 1)
    for args in (
        ["Não existe", "15/02/2026"],
        ["Soja", "30/02/2026"],
        ["Soja", "2026-02-15"],
        [],
    ):
        resposta = conversa.alerta(1, args, "pt")
        assert "Milho" in resposta[0] and "/alerta Milho 15/02/2026" in resposta[0]
    assert db.listar_alertas() == []


def test_testar_alerta_ignora_7_dias(ambiente):
    conversa, _, _, alertas, _ = ambiente
    chamadas = []
    alertas.verificar = lambda banco, hoje, forcar, chat_id: (
        chamadas.append((banco, hoje, forcar, chat_id))
        or [
            {
                "chat_id": "1",
                "alerta_id": 7,
                "mensagem_chave": "alerta_falta_agua",
                "valores": {"cultura": "Soja", "ks": 0.4, "dias": 2},
            }
        ]
    )
    db.criar_fazenda(1, 2, "BR", 1)
    resposta = conversa.testar_alerta(1, "pt")
    assert chamadas == [(db, date(2026, 11, 15), True, 1)]
    assert resposta == [t("alerta_falta_agua", "pt", cultura="Soja", ks=0.4, dias=2)]


def test_localizacao_fora_de_terra(ambiente):
    conversa, motor, *_ = ambiente
    id_ = db.criar_fazenda(1, 2, "BR", 1)

    def fora(lat, lon):
        raise ErroPontoInvalido("fora")

    motor.contexto = fora
    assert conversa.localizacao(1, 0, 0, "pt") == [t("ponto_invalido", "pt")]
    fazenda = db.fazenda_por_chat(1)
    assert (fazenda["id"], fazenda["lat"], fazenda["lon"]) == (id_, 1, 2)


def test_divide_mensagem_4096():
    for texto in ("a" * 4096, "a" * 4097, "🌱" * 4097, "a" * 4095 + "🌱" + "fim"):
        partes = dividir(texto)
        assert "".join(partes) == texto
        assert all(len(p) <= 4096 for p in partes)
    assert len(dividir("🌱" * 4096)) == 1
    assert len(dividir("🌱" * 4097)) == 2


def test_limite_mistura_comandos_e_texto_sem_contagem_dupla(ambiente):
    conversa, *_ = ambiente
    conversa.limite = Limite(maximo=2, relogio=lambda: 1000)
    db.criar_fazenda(1, 2, "BR", 1)
    assert conversa.start(1, [], "pt") == [t("boas_vindas", "pt")]
    assert conversa.texto(1, "pergunta", "pt") == ["Resposta do assistente"]
    assert conversa.alerta(1, ["Soja", "15/02/2026"], "pt") == [t("limite", "pt")]
    assert not db.listar_alertas()


def test_falha_ranking_mantem_fazenda_e_indisponibilidade_localizada(ambiente):
    conversa, motor, *_ = ambiente
    conversa.hoje = lambda: date(2028, 2, 29)

    def ranking(*args, **kwargs):
        raise ValueError("data inválida")

    motor.ranking_safra = ranking
    resposta = conversa.localizacao(1, 1, 2, "en")
    assert "unavailable" in resposta[0].lower()
    assert (db.fazenda_por_chat(1)["lat"], db.fazenda_por_chat(1)["lon"]) == (1, 2)


def test_ranking_fora_de_terra_preserva_fazenda(ambiente):
    conversa, motor, *_ = ambiente
    fazenda_id = db.criar_fazenda(1, 2, "BR", 1)

    def fora(*args, **kwargs):
        raise ErroPontoInvalido("fora")

    motor.ranking_safra = fora
    assert conversa.localizacao(1, 3, 4, "pt") == [t("ponto_invalido", "pt")]
    fazenda = db.fazenda_por_chat(1)
    assert (fazenda["id"], fazenda["lat"], fazenda["lon"]) == (fazenda_id, 1, 2)


def test_ranking_preliminar_inclui_aviso_traduzido(ambiente):
    conversa, motor, *_ = ambiente
    motor.ranking_safra = lambda *args, **kwargs: {
        "itens": [{"cultura": "Soja", "risco_pct": 10, "preliminar": True}]
    }
    for lang in ("pt", "en", "es"):
        resposta = conversa.localizacao(1, 1, 2, lang)
        assert t("aviso_preliminar", lang) in resposta[0]
        assert t("dados_fonte", lang) in resposta[0]


def test_alerta_cultura_incompleta_nao_inscreve(ambiente, monkeypatch):
    from core import culturas

    conversa, *_ = ambiente
    db.criar_fazenda(1, 2, "BR", 1)
    completo = culturas.carregar()["Soja"]
    monkeypatch.setattr(
        culturas, "carregar", lambda: {"Soja": completo, "Sem dados": {}}
    )
    resposta = conversa.alerta(1, ["Sem", "dados", "15/02/2026"], "pt")
    assert "Soja" in resposta[0] and "/alerta Milho 15/02/2026" in resposta[0]
    assert "Sem dados" not in resposta[0]
    assert db.listar_alertas() == []
