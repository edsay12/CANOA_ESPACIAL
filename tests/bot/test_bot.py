from datetime import UTC, time
from types import SimpleNamespace

import pytest

import bot


def test_job_diario_10_utc():
    chamadas = []
    fila = SimpleNamespace(
        run_daily=lambda callback, **kwargs: chamadas.append((callback, kwargs))
    )
    bot.agendar(fila, bot.job_verificar_alertas)
    assert len(chamadas) == 1
    assert chamadas[0][0] is bot.job_verificar_alertas
    assert chamadas[0][1]["time"] == time(10, 0, tzinfo=UTC)


def test_variaveis_ausentes():
    env = {
        "TELEGRAM_BOT_TOKEN": "fake",
        "GROQ_API_KEY": "fake",
        "MCP_TOKEN": "fake",
        "MCP_PUBLIC_URL": "https://example.test/mcp",
    }
    assert bot.verificar_ambiente(env) is None
    for nome in env:
        faltando = dict(env)
        faltando.pop(nome)
        with pytest.raises(SystemExit, match=nome):
            bot.verificar_ambiente(faltando)
        faltando[nome] = "  "
        with pytest.raises(SystemExit, match=nome):
            bot.verificar_ambiente(faltando)
    for url in ("http://example.test/mcp", "https://", "ftp://example.test"):
        with pytest.raises(SystemExit, match="MCP_PUBLIC_URL"):
            bot.verificar_ambiente({**env, "MCP_PUBLIC_URL": url})


def test_job_registra_somente_envio_confirmado(monkeypatch, tmp_path):
    import asyncio
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock

    from telegram.error import TelegramError

    from core import alertas, db

    monkeypatch.setenv("DB_PATH", str(tmp_path / "db.sqlite"))
    fazenda1 = db.criar_fazenda(1, 2, "BR", 1)
    fazenda2 = db.criar_fazenda(3, 4, "BR", 2)
    id1 = db.inscrever_alerta(fazenda1, "Soja", "2026-02-01", "es")
    id2 = db.inscrever_alerta(fazenda2, "Milho", "2026-02-01", "en")
    valores = {"cultura": "Soja", "ks": 0.4, "dias": 2}
    monkeypatch.setattr(
        alertas,
        "verificar",
        lambda banco, agora: [
            {
                "chat_id": "1",
                "alerta_id": id1,
                "mensagem_chave": "alerta_falta_agua",
                "valores": valores,
            },
            {
                "chat_id": "2",
                "alerta_id": id2,
                "mensagem_chave": "alerta_falta_agua",
                "valores": valores,
            },
            {
                "chat_id": "999",
                "alerta_id": id1,
                "mensagem_chave": "alerta_falta_agua",
                "valores": valores,
            },
        ],
    )

    async def thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", thread)
    envio = AsyncMock(side_effect=[TelegramError("falha"), None])
    ctx = SimpleNamespace(bot=SimpleNamespace(send_message=envio))
    antes = datetime.now(UTC)
    with pytest.raises(StopIteration):
        bot.job_verificar_alertas(ctx).send(None)
    registros = {a["id"]: a for a in db.listar_alertas()}
    assert registros[id1]["ultimo_envio"] is None
    assert datetime.fromisoformat(registros[id2]["ultimo_envio"]) >= antes
    assert envio.await_count == 2
    assert "Water shortage" in envio.await_args_list[1].kwargs["text"]


def test_foto_verifica_fazenda_e_envia_maior(monkeypatch, tmp_path):
    import asyncio
    from unittest.mock import AsyncMock

    from bot_logica.idioma import t
    from core import db

    monkeypatch.setenv("DB_PATH", str(tmp_path / "db.sqlite"))

    async def thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", thread)
    fotos = []
    fluxo = SimpleNamespace(
        tratar_foto=lambda *args: fotos.append(args) or ["foto descrita"]
    )
    limite = SimpleNamespace(permitir=lambda chat: True)
    maior = SimpleNamespace(width=400, height=300, file_id="maior")
    menor = SimpleNamespace(width=90, height=90, file_id="menor")
    msg = SimpleNamespace(
        photo=[maior, menor], caption="legenda", reply_text=AsyncMock()
    )
    update = SimpleNamespace(
        message=msg,
        effective_chat=SimpleNamespace(id=1),
        effective_user=SimpleNamespace(language_code="pt"),
    )
    arquivo = SimpleNamespace(
        download_as_bytearray=AsyncMock(return_value=bytearray(b"maior"))
    )
    telegram = SimpleNamespace(get_file=AsyncMock(return_value=arquivo))
    context = SimpleNamespace(
        application=SimpleNamespace(bot_data={"fotos": fluxo, "limite": limite}),
        bot=telegram,
    )
    with pytest.raises(StopIteration):
        bot.on_foto(update, context).send(None)
    telegram.get_file.assert_not_awaited()
    assert [c.args[0] for c in msg.reply_text.await_args_list] == [
        t("pedir_localizacao", "pt"),
        t("confirme_campo", "pt"),
    ]
    db.criar_fazenda(1, 2, "BR", 1)
    with pytest.raises(StopIteration):
        bot.on_foto(update, context).send(None)
    telegram.get_file.assert_awaited_once_with("maior")
    assert fotos[0][0:4] == ("1", b"maior", "legenda", "pt")
    msg.reply_text.assert_awaited_with("foto descrita")


@pytest.mark.parametrize("modo", ["ausente", "vazio", "personalizado"])
def test_configuracao_endpoints_e_modelos_voz(monkeypatch, modo):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    nomes = ("GROQ_CHAT_URL", "GROQ_TTS_URL", "GROQ_MODEL_CHAT", "GROQ_MODEL_TTS")
    personalizados = (
        "https://example.test/chat",
        "https://example.test/tts",
        "modelo-chat",
        "modelo-tts",
    )
    for nome, valor in zip(nomes, personalizados, strict=True):
        if modo == "ausente":
            monkeypatch.delenv(nome, raising=False)
        else:
            monkeypatch.setenv(nome, valor if modo == "personalizado" else "")
    chamadas = []

    class Resposta:
        content = b"wav"

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "resumo"}}]}

    def post(url, **kwargs):
        chamadas.append((url, kwargs))
        return Resposta()

    monkeypatch.setattr(bot.requests, "post", post)
    assert bot._resumir_para_voz("resposta fundamentada") == "resumo"
    assert bot.sintetizar_voz("spoken") == b"wav"
    esperados = (
        personalizados
        if modo == "personalizado"
        else (
            "https://api.groq.com/openai/v1/chat/completions",
            "https://api.groq.com/openai/v1/audio/speech",
            "openai/gpt-oss-120b",
            "canopylabs/orpheus-v1-english",
        )
    )
    assert (
        chamadas[0][0],
        chamadas[1][0],
        chamadas[0][1]["json"]["model"],
        chamadas[1][1]["json"]["model"],
    ) == esperados
    assert chamadas[0][1]["json"]["messages"][1]["content"] == "resposta fundamentada"
