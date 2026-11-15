"""Bot Telegram: conversa via Groq (Remote MCP), localização, fotos, áudio, alertas."""

import logging
import os
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import numpy as np
import pandas as pd
import requests

from core.db import criar_alerta, listar_alertas
from core import balanco, cache, culturas, power, solo
from core.db import listar_alertas

logger = logging.getLogger(__name__)

GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"

MENSAGENS_ALERTA = {
    "pt": (
        "⚠️ *Alerta de tendência de falta d'água*\n"
        "Sua lavoura de *{cultura}* está com déficit hídrico (Ks = {ks:.2f}) e faltam cerca de "
        "*{dias} dia(s)* para a fase crítica de florescimento.\n"
        "_Nota: os satélites da NASA POWER têm atraso de alguns dias; este aviso indica uma tendência recente._"
    ),
    "en": (
        "⚠️ *Water shortage trend alert*\n"
        "Your *{cultura}* crop is experiencing water stress (Ks = {ks:.2f}) with about "
        "*{dias} day(s)* left until the critical flowering stage.\n"
        "_Note: NASA POWER satellite data has a few days of latency; this alert reflects a recent trend._"
    ),
    "es": (
        "⚠️ *Alerta de tendencia de falta de agua*\n"
        "Tu cultivo de *{cultura}* presenta estrés hídrico (Ks = {ks:.2f}) y faltan unos "
        "*{dias} día(s)* para la etapa crítica de floración.\n"
        "_Nota: los datos de NASA POWER tienen unos días de retraso; este aviso indica una tendencia reciente._"
    ),
}


def _baixar_power_recente(lat: float, lon: float, dias: int = 50) -> pd.DataFrame:
    """Busca os últimos `dias` da NASA POWER com cache válido por 1 dia."""
    hoje = date.today()
    inicio = hoje - timedelta(days=dias)
    lat_r, lon_r = round(lat, 2), round(lon, 2)

    path = cache.caminho(f"alerta_{hoje.strftime('%Y%m%d')}", lat_r, lon_r)
    dados = cache.ler(path)

    if dados is None:
        params = {
            "parameters": ",".join(power.COLUNAS),
            "community": "AG",
            "latitude": lat_r,
            "longitude": lon_r,
            "start": inicio.strftime("%Y%m%d"),
            "end": hoje.strftime("%Y%m%d"),
            "format": "JSON",
        }
        r = requests.get(power.URL, params=params, timeout=60)
        r.raise_for_status()
        dados = r.json()
        cache.gravar(path, dados)

    p = dados["properties"]["parameter"]
    df = pd.DataFrame({nome: p.get(chave, {}) for chave, nome in power.COLUNAS.items()}).sort_index()
    df = df.replace(-999, np.nan).astype(float)
    df.insert(0, "data", pd.to_datetime(df.index, format="%Y%m%d"))
    # Remove os dias finais que ainda vieram totalmente vazios (latência da NASA)
    df = df.dropna(subset=["tmax", "tmin"]).reset_index(drop=True)
    return df


def _ks_atual(serie: pd.DataFrame, cultura: dict, cad_mm: float, data_plantio: str, lat: float) -> float | None:
    """Roda o balanço diário desde `data_plantio` até o último dia disponível e retorna o último Ks."""
    inicio_ts = pd.Timestamp(data_plantio)
    janela = serie[serie["data"] >= inicio_ts].copy()
    if janela.empty:
        return None

    chuva = janela["chuva"].fillna(0.0).to_numpy(float)
    temps = janela[["tmax", "tmin"]].interpolate(limit_direction="both").to_numpy(float)
    extra = janela.reindex(columns=["umid_rel", "vento", "pressao", "rad"]).to_numpy(float)
    doy = janela["data"].dt.day_of_year.to_numpy()

    taw = float(cad_mm) * float(cultura["raiz_m"])
    raw = float(cultura["p_deplecao"]) * taw
    dr = 0.5 * taw
    ks_ultimo = 1.0

    for i in range(len(janela)):
        etc = balanco.kc_diario(cultura, i + 1) * balanco.et0_dia(
            temps[i, 0], temps[i, 1], *extra[i], balanco.ra_mm(lat, doy[i])
        )
        ks_ultimo = 1.0 if dr <= raw else (taw - dr) / (taw - raw)
        eta = min(ks_ultimo * etc, taw - dr + chuva[i])
        dr = float(np.clip(dr - chuva[i] + eta, 0.0, taw))

    return float(np.clip(ks_ultimo, 0.0, 1.0))


def verificar_alertas() -> list[dict]:
    """Verifica inscrições ativas no SQLite e retorna [{"chat_id", "mensagem"}] para lavouras em risco."""
    inscricoes = listar_alertas()
    if not inscricoes:
        return []

    catalogo = culturas.carregar()
    hoje = date.today()
    alertas_disparar = []

    for item in inscricoes:
        nome_cultura = item["cultura"]
        cultura = catalogo.get(nome_cultura)
        if not cultura or not culturas.completa(cultura):
            continue

        data_plantio = date.fromisoformat(item["data_plantio"])
        dias_desde_plantio = (hoje - data_plantio).days
        if dias_desde_plantio < 0:
            continue

        # Início da fase de meio (florescimento) = dias_ini + dias_des
        inicio_meio = int(cultura["dias_ini"]) + int(cultura["dias_des"])
        dias_para_meio = inicio_meio - dias_desde_plantio

        # Critério da missão: faltam <= 15 dias para o início da fase de meio (e ainda não passou dela)
        if not (0 <= dias_para_meio <= 15):
            continue

        try:
            serie = _baixar_power_recente(item["lat"], item["lon"], dias=50)
            s = solo.agua_disponivel(item["lat"], item["lon"])
            ks = _ks_atual(serie, cultura, s["cad_mm"], item["data_plantio"], item["lat"])
        # Isola falhas de serviços externos ou cálculos para não interromper as demais inscrições.
        except Exception:
            logger.exception("Falha ao verificar alerta para a cultura %s", nome_cultura)
            continue

        if ks is not None and ks < 0.7:
            idioma = item.get("idioma") or "pt"
            template = MENSAGENS_ALERTA.get(idioma, MENSAGENS_ALERTA["en"])
            nome_exibicao = cultura.get(f"nome_{idioma}") or cultura.get("nome") or nome_cultura
            msg = template.format(cultura=nome_exibicao, ks=ks, dias=dias_para_meio)
            alertas_disparar.append({"chat_id": item["chat_id"], "mensagem": msg})

    return alertas_disparar


def transcrever(caminho_arquivo: str | Path, idioma: str | None = None) -> str:
    """Transcreve nota de voz (.ogg/.oga/.mp3/.wav) via Whisper na API da Groq."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Variável de ambiente GROQ_API_KEY não configurada.")

    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Áudio não encontrado: {caminho}")

    # Telegram salva notas de voz como .oga; renomeamos o filename no upload para .ogg (aceito nativamente pelo Whisper)
    nome_upload = f"{caminho.stem}.ogg" if caminho.suffix.lower() == ".oga" else caminho.name

    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"model": WHISPER_MODEL, "response_format": "text"}
    if idioma:
        data["language"] = idioma

    with open(caminho, "rb") as audio_file:
        files = {"file": (nome_upload, audio_file, "audio/ogg")}
        resp = requests.post(GROQ_AUDIO_URL, headers=headers, data=data, files=files, timeout=30)
        resp.raise_for_status()
        return resp.text.strip()

# --- Integração Telegram (Texto, Áudio STT + TTS Groq, Localização e Alertas) ---

import tempfile
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from bot_logica.idioma import idioma as detectar_idioma, t
from bot_logica.limite import Limite

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TTS_URL = "https://api.groq.com/openai/v1/audio/speech"
CHAT_MODEL = "openai/gpt-oss-120b"
TTS_MODEL = "canopylabs/orpheus-v1-english"
limite_mensagens = Limite()


def sintetizar_voz(texto: str) -> bytes:
    """Converte texto em inglês para áudio WAV usando Orpheus TTS na Groq."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada.")

    # Limita o tamanho para evitar erro de limite do modelo TTS
    texto_curto = texto.strip()[:190]
    resp = requests.post(
        GROQ_TTS_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": TTS_MODEL,
            "input": texto_curto,
            "voice": "troy",
            "response_format": "wav",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.content


def _perguntar_groq(
    texto_usuario: str,
    lang: str,
    coords: tuple[float, float] | None,
    para_audio: bool = False,
) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada.")

    contexto_local = (
        f"Coordenadas da fazenda (use apenas para identificar o município/região, NUNCA repita os números): lat={coords[0]:.4f}, lon={coords[1]:.4f}."
        if coords
        else "O usuário ainda não enviou a localização da fazenda."
    )

    if para_audio:
        sistema = (
            "You are Canoa Espacial's agricultural voice assistant. "
            "Write a short, natural spoken summary in English (STRICTLY under 180 characters, max 2 short sentences). "
            "NEVER read latitude, longitude, numbers, symbols, or bullet points. "
            f"Context: {contexto_local}"
        )
    else:
        sistema = (
            f"Você é o assistente agrícola da Canoa Espacial. Responda no idioma '{lang}' "
            "de forma bem organizada, visual e prática para produtores rurais. "
            "NUNCA escreva números de latitude ou longitude na resposta — cite apenas o nome da região/município. "
            "Organize obrigatoriamente nestes 3 blocos curtos com linha em branco entre eles:\n\n"
            "🌍 *Região e Clima:* (1 frase curta sobre o clima local)\n\n"
            "🌱 *O que plantar:* (lista curta com 3 a 4 culturas ideais)\n\n"
            "💧 *Dica rápida de manejo:* (1 orientação prática de água ou época de plantio)\n\n"
            f"{contexto_local}"
        )

    resp = requests.post(
        GROQ_CHAT_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": texto_usuario},
            ],
            "temperature": 0.4,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


async def _responder_consulta(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    texto: str,
    responder_com_audio: bool = False,
) -> None:
    lang = detectar_idioma(update.effective_user.language_code)
    chat_id = str(update.effective_chat.id)

    if not limite_mensagens.permitir(chat_id):
        await update.message.reply_text(t("limite", lang))
        return

    coords = context.user_data.get("coords")
    try:
        resposta = _perguntar_groq(texto, lang, coords, para_audio=False)
    except Exception as e:
        print(f"[Erro Groq Chat] {e}")
        await update.message.reply_text(t("llm_indisponivel", lang))
        return

    await update.message.reply_text(resposta, parse_mode="Markdown")

    if responder_com_audio:
        try:
            texto_en = _perguntar_groq(texto, "en", coords, para_audio=True)
            audio_bytes = sintetizar_voz(texto_en)
            await update.message.reply_audio(
                audio=audio_bytes,
                filename="resposta_canoa.wav",
                title="Canoa Espacial",
            )
        except Exception as e:
            print(f"[Aviso TTS] Não foi possível gerar áudio: {e}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = detectar_idioma(update.effective_user.language_code)
    await update.message.reply_text(t("boas_vindas", lang))


async def cmd_voz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    texto = " ".join(context.args).strip()
    if not texto:
        await update.message.reply_text("Use: /voz Your message in English")
        return
    try:
        audio_bytes = sintetizar_voz(texto)
        await update.message.reply_audio(
            audio=audio_bytes,
            filename="canoa_voz.wav",
            title="Canoa Espacial",
        )
    except Exception as e:
        await update.message.reply_text(f"Erro ao gerar áudio na Groq: {e}")


async def on_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = detectar_idioma(update.effective_user.language_code)
    loc = update.message.location
    context.user_data["coords"] = (loc.latitude, loc.longitude)
    await update.message.reply_text(
        f"📍 ({loc.latitude:.4f}, {loc.longitude:.4f}) — {t('dados_fonte', lang)}"
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _responder_consulta(update, context, update.message.text, responder_com_audio=False)


async def on_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = detectar_idioma(update.effective_user.language_code)
    midia = update.message.voice or update.message.audio
    arquivo_tg = await context.bot.get_file(midia.file_id)

    with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as tmp:
        caminho_tmp = Path(tmp.name)

    try:
        await arquivo_tg.download_to_drive(custom_path=str(caminho_tmp))
        texto_transcrito = transcrever(caminho_tmp, lang)
    except Exception:
        await update.message.reply_text(t("audio_falhou", lang))
        return
    finally:
        caminho_tmp.unlink(missing_ok=True)

    await update.message.reply_text(f"🎙️ _{texto_transcrito}_", parse_mode="Markdown")
    await _responder_consulta(update, context, texto_transcrito, responder_com_audio=True)


async def cmd_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = detectar_idioma(update.effective_user.language_code)
    coords = context.user_data.get("coords")
    if not coords:
        await update.message.reply_text(t("pedir_localizacao", lang))
        return

    catalogo = culturas.carregar()
    nomes_validos = [k for k, v in catalogo.items() if culturas.completa(v)]

    if len(context.args) < 2:
        await update.message.reply_text(
            t("alerta_formato", lang, culturas=", ".join(nomes_validos[:8]))
        )
        return

    cultura_nome = context.args[0].capitalize()
    data_str = context.args[1]
    try:
        data_iso = datetime.strptime(data_str, "%d/%m/%Y").date().isoformat()
    except ValueError:
        await update.message.reply_text(
            t("alerta_formato", lang, culturas=", ".join(nomes_validos[:8]))
        )
        return

    criar_alerta(str(update.effective_chat.id), coords[0], coords[1], cultura_nome, data_iso, lang)
    await update.message.reply_text(t("alerta_ok", lang, cultura=cultura_nome, data=data_str))


async def job_verificar_alertas(context: ContextTypes.DEFAULT_TYPE) -> None:
    for alerta in verificar_alertas():
        await context.bot.send_message(
            chat_id=alerta["chat_id"],
            text=alerta["mensagem"],
            parse_mode="Markdown",
        )


def iniciar_bot() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Variável de ambiente TELEGRAM_BOT_TOKEN não configurada.")

    app = (
        Application.builder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("alerta", cmd_alerta))
    app.add_handler(CommandHandler("voz", cmd_voz))
    app.add_handler(MessageHandler(filters.LOCATION, on_location))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    if app.job_queue:
        app.job_queue.run_repeating(job_verificar_alertas, interval=21600, first=15)

    print("Bot da Canoa Espacial rodando no Telegram... (Ctrl+C para parar)")
    app.run_polling()


if __name__ == "__main__":
    iniciar_bot()
