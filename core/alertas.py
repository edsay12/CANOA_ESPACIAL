"""Situação hídrica recente e seleção de alertas por fazenda."""

import logging
from datetime import UTC, date, datetime, time, timedelta

import pandas as pd

from core import balanco, culturas, recente, solo
from core.erros import ErroFonteDados

log = logging.getLogger(__name__)


def _data(hoje):
    if isinstance(hoje, datetime):
        return _utc(hoje).date()
    return hoje


def _utc(valor):
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor)
    if isinstance(valor, date) and not isinstance(valor, datetime):
        valor = datetime.combine(valor, time.min, tzinfo=UTC)
    if not isinstance(valor, datetime):
        raise TypeError("Data de envio inválida")
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=UTC)
    return valor.astimezone(UTC)


def situacao(lat, lon, cultura, data_plantio, hoje):
    hoje = _data(hoje)
    plantio = date.fromisoformat(data_plantio)
    if plantio > hoje:
        raise ValueError("Plantio futuro")
    catalogo = culturas.carregar()
    parametros = catalogo.get(cultura)
    if not parametros or not culturas.completa(parametros):
        raise ValueError(f"Cultura desconhecida ou incompleta: {cultura}")
    dias = (hoje - plantio).days + 1
    serie = recente.serie(lat, lon, dias=max(45, dias), hoje=hoje)
    janela = serie[
        (serie["data"] >= pd.Timestamp(plantio)) & (serie["data"] <= pd.Timestamp(hoje))
    ].copy()
    validas = janela["tmax"].notna() & janela["tmin"].notna()
    if not validas.any():
        raise ValueError("Série sem temperaturas observadas")
    janela = janela.loc[: validas[validas].index[-1]]
    if janela.empty or janela["data"].iloc[0] != pd.Timestamp(plantio):
        raise ValueError("Série não cobre a data de plantio")
    if len(janela) != (janela["data"].iloc[-1].date() - plantio).days + 1:
        raise ValueError("Série não cobre todos os dias desde o plantio")
    cad = solo.agua_disponivel(lat, lon)["cad_mm"]
    ks = balanco.balanco_parcial(janela, parametros, cad, lat)["ks"]
    dias_meio = (
        int(parametros["dias_ini"])
        + int(parametros["dias_des"])
        - (hoje - plantio).days
    )
    return {
        "ks": ks,
        "dias_ate_meio": dias_meio,
        "alerta": ks < 0.7 and 0 <= dias_meio <= 15,
    }


def _local(item):
    return (str(item.get("chat_id")), item.get("lat"), item.get("lon"))


def _grupo(item, fazendas_por_local):
    if item.get("fazenda_id") is not None:
        return ("fazenda", item["fazenda_id"])
    fazenda_id = fazendas_por_local.get(_local(item))
    if fazenda_id is not None:
        return ("fazenda", fazenda_id)
    return ("legado", *_local(item))


def verificar(db, hoje, forcar=False, chat_id=None):
    itens = db.listar_alertas(ativos=False)
    fazendas_por_local = {
        _local(item): item["fazenda_id"]
        for item in itens
        if item.get("fazenda_id") is not None and item.get("chat_id")
    }
    instante = _utc(hoje)
    ultimos = {}
    for item in itens:
        if not item.get("ultimo_envio"):
            continue
        try:
            envio = _utc(item["ultimo_envio"])
        except (TypeError, ValueError):
            log.warning("Data de envio inválida para alerta %s", item.get("id"))
            continue
        chave = _grupo(item, fazendas_por_local)
        ultimos[chave] = max(ultimos.get(chave, envio), envio)
    candidatos = []
    selecionados = set()
    for item in itens:
        if not item.get("ativo") or not item.get("chat_id"):
            continue
        if chat_id is not None and str(item["chat_id"]) != str(chat_id):
            continue
        chave = _grupo(item, fazendas_por_local)
        if not forcar and chave in selecionados:
            continue
        if (
            not forcar
            and chave in ultimos
            and instante - ultimos[chave] < timedelta(days=7)
        ):
            continue
        try:
            status = situacao(
                item["lat"], item["lon"], item["cultura"], item["data_plantio"], hoje
            )
        except (ErroFonteDados, ValueError) as erro:
            log.warning("Não foi possível verificar alerta %s: %s", item["id"], erro)
            continue
        if status["alerta"]:
            candidatos.append(
                {
                    "chat_id": item["chat_id"],
                    "alerta_id": item["id"],
                    "mensagem_chave": "alerta_falta_agua",
                    "valores": {
                        "cultura": item["cultura"],
                        "ks": status["ks"],
                        "dias": status["dias_ate_meio"],
                    },
                }
            )
            selecionados.add(chave)
    return candidatos
