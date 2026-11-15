import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import requests
from pytest import raises

import bot
from bot_logica.audio import Audio
from bot_logica.conversa import Conversa
from bot_logica.idioma import t
from bot_logica.limite import Limite
from bot_logica.llm import LLMIndisponivel
from core import alertas, culturas, db


def executar(corrotina):
    with raises(StopIteration):
        corrotina.send(None)


@pytest.fixture
def ambiente(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "teste.sqlite"))

    def rede_proibida(*args, **kwargs):
        raise AssertionError("rede não simulada")

    monkeypatch.setattr(requests, "post", rede_proibida)

    async def thread(funcao, *args, **kwargs):
        return funcao(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", thread)
    resposta = SimpleNamespace(
        reply_text=AsyncMock(),
        reply_audio=AsyncMock(),
        text="Qual cultura?",
        location=None,
        voice=None,
        audio=None,
        photo=[],
        caption=None,
    )
    update = SimpleNamespace(
        message=resposta,
        effective_chat=SimpleNamespace(id=123),
        effective_user=SimpleNamespace(language_code="es"),
    )
    assistente = SimpleNamespace(responder=lambda *args: "Resultado com fonte NASA")
    limite = Limite(maximo=100)
    motor = SimpleNamespace(
        contexto=lambda lat, lon: {"pais": {"iso2": "BR"}},
        clima_mudou=lambda *args, **kwargs: {"resumo": "clima"},
        ranking_safra=lambda *args, **kwargs: {
            "itens": [{"cultura": "Soja", "risco_pct": 10}]
        },
    )
    conversa = Conversa(db, motor, assistente, limite, alertas)
    audio = Audio(conversa, lambda conteudo, **kwargs: "Pergunta transcrita")
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={
                "assistente": assistente,
                "conversa": conversa,
                "limite": limite,
                "audio": audio,
            }
        ),
        user_data={},
        args=[],
        bot=None,
    )
    return update, context


def test_sem_fazenda_nao_chama_assistente(ambiente):
    update, context = ambiente
    chamadas = []
    context.application.bot_data["assistente"].responder = lambda *args: (
        chamadas.append(args)
    )
    executar(bot.on_text(update, context))
    assert not chamadas
    update.message.reply_text.assert_awaited_once_with(t("pedir_localizacao", "es"))


def test_localizacao_persistida_atualizada_e_consulta(ambiente):
    update, context = ambiente
    update.message.location = SimpleNamespace(latitude=-12.0, longitude=-45.0)
    executar(bot.on_location(update, context))
    primeira = db.fazenda_por_chat(123)
    assert (primeira["lat"], primeira["lon"], primeira["pais"]) == (-12.0, -45.0, "BR")
    update.message.location = SimpleNamespace(latitude=-13.0, longitude=-46.0)
    executar(bot.on_location(update, context))
    atual = db.fazenda_por_chat(123)
    assert atual["id"] == primeira["id"]
    assert (atual["lat"], atual["lon"]) == (-13.0, -46.0)
    chamadas = []
    context.application.bot_data["assistente"].responder = lambda *args: (
        chamadas.append(args) or "Resposta NASA"
    )
    executar(bot.on_text(update, context))
    assert chamadas == [("123", "Qual cultura?", atual, "es")]
    update.message.reply_text.assert_awaited_with("Resposta NASA")


def test_audio_transcrito_usa_assistente_reutilizado(ambiente, monkeypatch):
    update, context = ambiente
    fazenda_id = db.criar_fazenda(1, 2, "BR", 123)
    chamadas = []
    context.application.bot_data["assistente"].responder = lambda *args: (
        chamadas.append(args) or "Resposta NASA"
    )
    update.message.voice = SimpleNamespace(file_id="a")
    arquivo = SimpleNamespace(
        download_as_bytearray=AsyncMock(return_value=bytearray(b"ogg"))
    )
    context.bot = SimpleNamespace(get_file=AsyncMock(return_value=arquivo))
    falado = []
    resumido = []
    monkeypatch.setattr(
        bot,
        "_resumir_para_voz",
        lambda texto: resumido.append(texto) or "Grounded English summary",
        raising=False,
    )
    monkeypatch.setattr(
        bot, "sintetizar_voz", lambda texto: falado.append(texto) or b"audio"
    )
    executar(bot.on_audio(update, context))
    update.message.reply_text.assert_any_await("🎙️ Pergunta transcrita")
    assert chamadas[0][1] == "Pergunta transcrita"
    assert chamadas[0][2]["id"] == fazenda_id
    assert resumido == ["Resposta NASA"]
    assert falado == ["Grounded English summary"]
    update.message.reply_audio.assert_awaited_once()


def test_falhas_localizadas_e_audio(ambiente, monkeypatch):
    update, context = ambiente
    db.criar_fazenda(1, 2, "BR", 123)

    def falhar(*args):
        raise LLMIndisponivel("segredo")

    context.application.bot_data["assistente"].responder = falhar
    executar(bot.on_text(update, context))
    assert update.message.reply_text.await_args_list[-1].args[0] == t(
        "llm_indisponivel", "es"
    )
    context.application.bot_data["conversa"].assistente = None
    executar(bot.on_text(update, context))
    assert update.message.reply_text.await_args_list[-1].args[0] == t(
        "llm_indisponivel", "es"
    )
    context.args = ["hello"]

    def tts_falha(texto):
        raise requests.RequestException("segredo")

    monkeypatch.setattr(bot, "sintetizar_voz", tts_falha)
    executar(bot.cmd_voz(update, context))
    assert "segredo" not in update.message.reply_text.await_args_list[-1].args[0]


def test_alerta_usa_fazenda_idioma_e_valida_cultura(ambiente):
    update, context = ambiente
    fazenda_id = db.criar_fazenda(1, 2, "BR", 123)
    context.args = ["Soja", "15/02/2026"]
    executar(bot.cmd_alerta(update, context))
    alerta = db.listar_alertas()[0]
    assert (
        alerta["fazenda_id"],
        alerta["idioma"],
        alerta["cultura"],
        alerta["data_plantio"],
    ) == (fazenda_id, "es", "Soja", "2026-02-15")
    update.message.location = SimpleNamespace(latitude=3, longitude=4)
    executar(bot.on_location(update, context))
    atualizado = db.listar_alertas()[0]
    assert atualizado["id"] == alerta["id"]
    assert (
        atualizado["fazenda_id"],
        atualizado["lat"],
        atualizado["lon"],
        atualizado["idioma"],
    ) == (fazenda_id, 3, 4, "es")
    context.args = ["Inexistente", "15/02/2026"]
    executar(bot.cmd_alerta(update, context))
    assert len(db.listar_alertas()) == 1
    assert (
        t(
            "alerta_formato",
            "es",
            culturas=", ".join(
                [k for k, v in culturas.carregar().items() if culturas.completa(v)]
            ),
        )
        == update.message.reply_text.await_args_list[-1].args[0]
    )


def test_audio_sem_fazenda_e_falha_nao_gera_voz(ambiente, monkeypatch):
    update, context = ambiente
    update.message.voice = SimpleNamespace(file_id="a")
    context.bot = SimpleNamespace(
        get_file=AsyncMock(
            return_value=SimpleNamespace(
                download_as_bytearray=AsyncMock(return_value=bytearray(b"ogg"))
            )
        )
    )
    context.application.bot_data["audio"].transcrever = lambda conteudo, **kwargs: (
        "Pergunta"
    )
    executar(bot.on_audio(update, context))
    update.message.reply_audio.assert_not_awaited()
    assert update.message.reply_text.await_args_list[-1].args[0] == t(
        "pedir_localizacao", "es"
    )
    db.criar_fazenda(1, 2, "BR", 123)

    def falhar(*args):
        raise LLMIndisponivel("erro")

    context.application.bot_data["assistente"].responder = falhar
    executar(bot.on_audio(update, context))
    update.message.reply_audio.assert_not_awaited()
    assert update.message.reply_text.await_args_list[-1].args[0] == t(
        "llm_indisponivel", "es"
    )


def test_inicializacao_reutiliza_assistente_e_recusa_sem_mcp(monkeypatch):
    class App:
        def __init__(self):
            self.bot_data = {}
            self.job_queue = SimpleNamespace(run_daily=lambda *args, **kwargs: None)
            self.handlers = []
            self.rodou = False

        def add_handler(self, handler):
            self.handlers.append(handler)

        def run_polling(self):
            self.rodou = True

    apps = []

    class Builder:
        def token(self, *args):
            return self

        def connect_timeout(self, *args):
            return self

        def read_timeout(self, *args):
            return self

        def write_timeout(self, *args):
            return self

        def build(self):
            app = App()
            apps.append(app)
            return app

    monkeypatch.setattr(bot.Application, "builder", lambda: Builder())
    monkeypatch.setattr(bot, "load_dotenv", lambda: None)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake")
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    monkeypatch.setenv("GROQ_MODEL_CHAT", "fake-model")
    monkeypatch.setenv("MCP_PUBLIC_URL", "https://example.test/mcp")
    monkeypatch.setenv("MCP_TOKEN", "fake-mcp")
    monkeypatch.setattr(bot, "OpenAI", lambda **kw: "fake-client")
    assistente = object()
    argumentos = []
    monkeypatch.setattr(
        bot, "Assistente", lambda *args: argumentos.append(args) or assistente
    )
    monkeypatch.setattr(bot, "VisaoGroq", lambda *args: "visao")
    monkeypatch.setattr(bot, "TranscritorGroq", lambda *args: "stt")
    bot.iniciar_bot()
    assert apps[-1].rodou
    assert argumentos == [
        ("fake-client", "fake-model", "https://example.test/mcp", "fake-mcp")
    ]
    assert apps[-1].bot_data["conversa"].assistente is assistente
    assert len(apps[-1].handlers) > 0
    monkeypatch.delenv("MCP_TOKEN")
    with pytest.raises(SystemExit, match="MCP_TOKEN"):
        bot.iniciar_bot()
    assert len(apps) == 1


def test_resumo_usa_apenas_resposta_fundamentada(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    chamadas = []

    class Resposta:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "Faithful summary"}}]}

    def post(url, **kwargs):
        chamadas.append(kwargs["json"]["messages"])
        return Resposta()

    monkeypatch.setattr(requests, "post", post)
    assert bot._resumir_para_voz("Resposta fundamentada NASA") == "Faithful summary"
    assert chamadas[0][1] == {"role": "user", "content": "Resposta fundamentada NASA"}
    assert "Do not add facts, recommendations" in chamadas[0][0]["content"]


def test_alerta_sem_destinatario_nao_consulta_dados(monkeypatch):
    monkeypatch.setattr(
        alertas, "situacao", lambda *args: pytest.fail("não deve consultar")
    )
    banco = SimpleNamespace(
        listar_alertas=lambda ativos: [{"chat_id": None, "cultura": "Soja", "ativo": 1}]
    )
    from datetime import date

    assert alertas.verificar(banco, date(2026, 11, 15)) == []


def test_audio_bloqueado_antes_de_download_e_uma_contagem_no_sucesso(
    ambiente, monkeypatch
):
    update, context = ambiente
    db.criar_fazenda(1, 2, "BR", 123)
    update.message.voice = SimpleNamespace(file_id="a")
    arquivo = SimpleNamespace(
        download_as_bytearray=AsyncMock(return_value=bytearray(b"ogg"))
    )
    context.bot = SimpleNamespace(get_file=AsyncMock(return_value=arquivo))
    limite = Limite(maximo=1, relogio=lambda: 100)
    context.application.bot_data["limite"] = limite
    context.application.bot_data["conversa"].limite = limite
    transcricoes = []
    context.application.bot_data["audio"].transcrever = lambda *args, **kwargs: (
        transcricoes.append(args) or "pergunta"
    )
    monkeypatch.setattr(bot, "_resumir_para_voz", lambda texto: "summary")
    monkeypatch.setattr(bot, "sintetizar_voz", lambda texto: b"wav")
    executar(bot.on_audio(update, context))
    assert transcricoes == [(b"ogg",)]
    update.message.reply_text.assert_any_await("Resultado com fonte NASA")
    executar(bot.on_audio(update, context))
    assert context.bot.get_file.await_count == 1
    assert len(transcricoes) == 1
    update.message.reply_text.assert_awaited_with(t("limite", "es"))


def test_falha_no_download_conta_uma_vez_e_retorna_mensagem(ambiente):
    update, context = ambiente
    update.message.voice = SimpleNamespace(file_id="a")
    context.bot = SimpleNamespace(
        get_file=AsyncMock(side_effect=RuntimeError("arquivo indisponível"))
    )
    limite = Limite(maximo=1, relogio=lambda: 100)
    context.application.bot_data["limite"] = limite
    context.application.bot_data["conversa"].limite = limite
    executar(bot.on_audio(update, context))
    update.message.reply_text.assert_awaited_with(t("audio_falhou", "es"))
    executar(bot.on_audio(update, context))
    assert context.bot.get_file.await_count == 1
    update.message.reply_text.assert_awaited_with(t("limite", "es"))
