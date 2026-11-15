"""Ligação dos fluxos de conversa, fotos e áudio ao Telegram."""

import asyncio
import logging
import os
from datetime import UTC, datetime, time
from types import SimpleNamespace
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv
from openai import OpenAI
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot_logica.audio import Audio, TranscritorGroq
from bot_logica.conversa import Conversa, dividir
from bot_logica.fotos import Fotos, VisaoGroq, maior_foto
from bot_logica.idioma import idioma as detectar_idioma
from bot_logica.idioma import t
from bot_logica.limite import Limite
from bot_logica.llm import Assistente
from core import alertas, clima, contexto, db, modelo

logger = logging.getLogger(__name__)

DEFAULT_GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_TTS_URL = "https://api.groq.com/openai/v1/audio/speech"
DEFAULT_CHAT_MODEL = "openai/gpt-oss-120b"
DEFAULT_TTS_MODEL = "canopylabs/orpheus-v1-english"


def sintetizar_voz(texto: str) -> bytes:
    """Converte texto em inglês para áudio WAV usando Orpheus TTS na Groq."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada.")

    # Limita o tamanho para evitar erro de limite do modelo TTS
    texto_curto = texto.strip()[:190]
    resp = requests.post(
        os.environ.get("GROQ_TTS_URL") or DEFAULT_GROQ_TTS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.environ.get("GROQ_MODEL_TTS") or DEFAULT_TTS_MODEL,
            "input": texto_curto,
            "voice": "troy",
            "response_format": "wav",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.content


def _resumir_para_voz(resposta: str) -> str:
    """Resume somente a resposta já fundamentada para o TTS em inglês."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada")
    resp = requests.post(
        os.environ.get("GROQ_CHAT_URL") or DEFAULT_GROQ_CHAT_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": os.environ.get("GROQ_MODEL_CHAT") or DEFAULT_CHAT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Summarize the supplied answer faithfully in spoken English, "
                    "under 180 characters. Do not add facts, recommendations, or numbers.",
                },
                {"role": "user", "content": resposta},
            ],
            "temperature": 0,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def verificar_ambiente(env):
    for nome in ("TELEGRAM_BOT_TOKEN", "GROQ_API_KEY", "MCP_TOKEN", "MCP_PUBLIC_URL"):
        if not env.get(nome, "").strip():
            raise SystemExit(f"Variável obrigatória ausente: {nome}")
    try:
        url = urlsplit(env["MCP_PUBLIC_URL"])
        valida = url.scheme == "https" and url.netloc and url.hostname
    except ValueError:
        valida = False
    if not valida:
        raise SystemExit("MCP_PUBLIC_URL deve ser uma URL HTTPS válida")


def agendar(job_queue, verificar):
    job_queue.run_daily(verificar, time=time(10, 0, tzinfo=UTC))


def _dados(update, context):
    return (
        str(update.effective_chat.id),
        detectar_idioma(update.effective_user.language_code),
        context.application.bot_data,
    )


async def _enviar(update, mensagens):
    for mensagem in mensagens:
        await update.message.reply_text(mensagem)


async def cmd_start(update, context):
    chat, lang, dados = _dados(update, context)
    await _enviar(
        update,
        await asyncio.to_thread(dados["conversa"].start, chat, context.args, lang),
    )


async def cmd_alerta(update, context):
    chat, lang, dados = _dados(update, context)
    await _enviar(
        update,
        await asyncio.to_thread(dados["conversa"].alerta, chat, context.args, lang),
    )


async def cmd_testar_alerta(update, context):
    chat, lang, dados = _dados(update, context)
    await _enviar(
        update, await asyncio.to_thread(dados["conversa"].testar_alerta, chat, lang)
    )


async def on_location(update, context):
    chat, lang, dados = _dados(update, context)
    loc = update.message.location
    await _enviar(
        update,
        await asyncio.to_thread(
            dados["conversa"].localizacao, chat, loc.latitude, loc.longitude, lang
        ),
    )


async def on_text(update, context):
    chat, lang, dados = _dados(update, context)
    await _enviar(
        update,
        await asyncio.to_thread(
            dados["conversa"].texto, chat, update.message.text, lang
        ),
    )


async def cmd_voz(update, context):
    chat, lang, dados = _dados(update, context)
    if not dados["limite"].permitir(chat):
        await _enviar(update, [t("limite", lang)])
        return
    texto = " ".join(context.args).strip()
    if not texto:
        await update.message.reply_text("Use: /voz Your message in English")
        return
    try:
        audio = await asyncio.to_thread(sintetizar_voz, texto)
        await update.message.reply_audio(
            audio=audio, filename="canoa_voz.wav", title="Canoa Espacial"
        )
    except (requests.RequestException, RuntimeError, TelegramError):
        await update.message.reply_text(t("llm_indisponivel", lang))


async def on_foto(update, context):
    chat, lang, dados = _dados(update, context)
    if not dados["limite"].permitir(chat):
        await _enviar(update, [t("limite", lang), t("confirme_campo", lang)])
        return
    fazenda = await asyncio.to_thread(db.fazenda_por_chat, chat)
    if fazenda is None:
        await _enviar(update, [t("pedir_localizacao", lang), t("confirme_campo", lang)])
        return
    try:
        foto = maior_foto(update.message.photo)
        arquivo = await context.bot.get_file(foto.file_id)
        conteudo = bytes(await arquivo.download_as_bytearray())
    except (TelegramError, OSError, RuntimeError):
        await _enviar(update, [t("foto_falhou", lang), t("confirme_campo", lang)])
        return
    mensagens = await asyncio.to_thread(
        dados["fotos"].tratar_foto,
        chat,
        conteudo,
        update.message.caption,
        lang,
        datetime.now(UTC),
    )
    await _enviar(update, mensagens)


async def on_audio(update, context):
    chat, lang, dados = _dados(update, context)
    if not dados["limite"].permitir(chat):
        await _enviar(update, [t("limite", lang)])
        return
    midia = update.message.voice or update.message.audio
    try:
        arquivo = await context.bot.get_file(midia.file_id)
        conteudo = bytes(await arquivo.download_as_bytearray())
    except (TelegramError, OSError, RuntimeError):
        await _enviar(update, [t("audio_falhou", lang)])
        return
    nome = getattr(midia, "file_name", None) or "voz.ogg"
    transcricao, respostas = await asyncio.to_thread(
        dados["audio"].processar_voz, chat, conteudo, lang, nome, limite_verificado=True
    )
    if transcricao is not None:
        await _enviar(update, dividir(f"🎙️ {transcricao}"))
    await _enviar(update, respostas)
    erros = {
        t(chave, lang)
        for chave in ("audio_falhou", "pedir_localizacao", "llm_indisponivel", "limite")
    }
    if (
        transcricao
        and respostas
        and not any(resposta in erros for resposta in respostas)
    ):
        try:
            resumo = await asyncio.to_thread(_resumir_para_voz, "".join(respostas))
            voz = await asyncio.to_thread(sintetizar_voz, resumo)
            await update.message.reply_audio(
                audio=voz, filename="resposta_canoa.wav", title="Canoa Espacial"
            )
        except (
            requests.RequestException,
            RuntimeError,
            TelegramError,
            ValueError,
            KeyError,
            IndexError,
        ):
            logger.warning("Não foi possível gerar resposta em áudio")


async def job_verificar_alertas(context):
    agora = datetime.now(UTC)
    candidatos = await asyncio.to_thread(alertas.verificar, db, agora)
    inscricoes = await asyncio.to_thread(db.listar_alertas)
    inscricoes_por_id = {item["id"]: item for item in inscricoes}
    for candidato in candidatos:
        inscricao = inscricoes_por_id.get(candidato["alerta_id"])
        if not inscricao or str(inscricao.get("chat_id")) != str(candidato["chat_id"]):
            continue
        idioma = inscricao.get("idioma") or "pt"
        mensagem = t(candidato["mensagem_chave"], idioma, **candidato["valores"])
        try:
            await context.bot.send_message(chat_id=candidato["chat_id"], text=mensagem)
        except TelegramError:
            logger.warning("Falha ao entregar alerta %s", candidato["alerta_id"])
            continue
        await asyncio.to_thread(
            db.marcar_alerta_enviado, candidato["alerta_id"], datetime.now(UTC)
        )


def main():
    load_dotenv()
    verificar_ambiente(os.environ)
    cliente = OpenAI(api_key=os.environ["GROQ_API_KEY"])
    assistente = Assistente(
        cliente,
        os.environ.get("GROQ_MODEL_CHAT") or DEFAULT_CHAT_MODEL,
        os.environ["MCP_PUBLIC_URL"],
        os.environ["MCP_TOKEN"],
    )
    limite = Limite()
    motor = SimpleNamespace(
        contexto=contexto.contexto,
        clima_mudou=clima.clima_mudou,
        ranking_safra=modelo.ranking_safra,
    )
    conversa = Conversa(db, motor, assistente, limite, alertas)
    fotos = Fotos(
        db,
        VisaoGroq(cliente, os.environ.get("GROQ_MODEL_VISION") or "qwen/qwen3.8-27b"),
        alertas,
    )
    audio = Audio(
        conversa,
        TranscritorGroq(
            cliente, os.environ.get("GROQ_MODEL_AUDIO") or "whisper-large-v3-turbo"
        ),
    )
    app = (
        Application.builder()
        .token(os.environ["TELEGRAM_BOT_TOKEN"])
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )
    app.bot_data.update(conversa=conversa, fotos=fotos, audio=audio, limite=limite)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("alerta", cmd_alerta))
    app.add_handler(CommandHandler("testar_alerta", cmd_testar_alerta))
    app.add_handler(CommandHandler("voz", cmd_voz))
    app.add_handler(MessageHandler(filters.LOCATION, on_location))
    app.add_handler(MessageHandler(filters.PHOTO, on_foto))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    if app.job_queue is None:
        raise RuntimeError("JobQueue não disponível")
    agendar(app.job_queue, job_verificar_alertas)
    app.run_polling()


iniciar_bot = main


if __name__ == "__main__":
    main()
