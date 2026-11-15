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
