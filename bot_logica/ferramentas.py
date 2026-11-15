"""Ferramentas do motor e seus contratos para MCP e chamadas locais."""

import re
from datetime import date

from jsonschema import ValidationError, validate

from bot_logica.idioma import t
from core import clima, culturas, db, modelo
from core import contexto as contexto_motor
from core.erros import ErroFonteDados, ErroPontoInvalido


def contexto(lat, lon):
    return contexto_motor.contexto(lat=lat, lon=lon)


def clima_mudou(lat, lon, idioma="pt"):
    return clima.clima_mudou(lat=lat, lon=lon, idioma=idioma)


def ranking_safra(lat, lon, data_semeadura, prioridades=None, idioma="pt"):
    return modelo.ranking_safra(
        lat=lat,
        lon=lon,
        data_semeadura=data_semeadura,
        prioridades=prioridades,
        idioma=idioma,
    )


def planos_rotacao(
    lat, lon, historico, prioridades=None, idioma="pt", data_semeadura=None
):
    return modelo.planos_rotacao(
        lat=lat,
        lon=lon,
        historico=historico,
        prioridades=prioridades,
        idioma=idioma,
        data_semeadura=data_semeadura,
    )


def janela_plantio(lat, lon, cultura, idioma="pt"):
    return clima.janela_plantio(lat=lat, lon=lon, cultura=cultura)


def info_cultura(nome):
    catalogo = culturas.carregar()
    if nome not in catalogo:
        raise ValueError(
            f"Cultura desconhecida: {nome}. Culturas conhecidas: {', '.join(sorted(catalogo))}"
        )
    campos = (
        "papel",
        "familia",
        "fixa_n",
        "climas",
        "tolerancia_seca",
        "efeito_solo",
        "fonte",
    )
    return {campo: catalogo[nome][campo] for campo in campos}


def registrar_observacao(fazenda_id, texto):
    if db.fazenda(fazenda_id) is None:
        raise ValueError("Fazenda não encontrada")
    identificador = db.salvar_observacao(fazenda_id, texto, None, None)
    return {"id": identificador}


def inscrever_alerta(fazenda_id, cultura, data_plantio):
    if cultura not in culturas.carregar():
        raise ValueError(f"Cultura desconhecida: {cultura}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data_plantio):
        raise ValueError("data_plantio deve usar YYYY-MM-DD")
    date.fromisoformat(data_plantio)
    return {"id": db.inscrever_alerta(fazenda_id, cultura, data_plantio)}


def _schema(properties, required):
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


_COORDS = {
    "lat": {"type": "number", "description": "Latitude"},
    "lon": {"type": "number", "description": "Longitude"},
}
_IDIOMA = {
    "type": "string",
    "enum": ["pt", "en", "es"],
    "description": "Idioma / language",
}
_PRIORIDADES = {
    "type": "object",
    "description": "Prioridades / priorities",
    "properties": {
        chave: {"type": "number"} for chave in ("retorno", "seguranca", "solo")
    },
    "additionalProperties": False,
}

FERRAMENTAS = {
    "contexto": {
        "funcao": contexto,
        "descricao_pt_en": {
            "pt": "Obtém o contexto do local.",
            "en": "Get location context.",
        },
        "schema": _schema({**_COORDS}, ["lat", "lon"]),
    },
    "clima_mudou": {
        "funcao": clima_mudou,
        "descricao_pt_en": {
            "pt": "Mostra mudanças do clima.",
            "en": "Show climate changes.",
        },
        "schema": _schema({**_COORDS, "idioma": _IDIOMA}, ["lat", "lon"]),
    },
    "ranking_safra": {
        "funcao": ranking_safra,
        "descricao_pt_en": {
            "pt": "Compara culturas para uma safra.",
            "en": "Compare crops for a season.",
        },
        "schema": _schema(
            {
                **_COORDS,
                "data_semeadura": {"type": "string", "description": "MM-DD"},
                "prioridades": _PRIORIDADES,
                "idioma": _IDIOMA,
            },
            ["lat", "lon", "data_semeadura"],
        ),
    },
    "planos_rotacao": {
        "funcao": planos_rotacao,
        "descricao_pt_en": {
            "pt": "Compara planos de rotação.",
            "en": "Compare crop rotation plans.",
        },
        "schema": _schema(
            {
                **_COORDS,
                "historico": {"type": "array", "items": {"type": "string"}},
                "prioridades": _PRIORIDADES,
                "idioma": _IDIOMA,
                "data_semeadura": {"type": "string", "description": "MM-DD"},
            },
            ["lat", "lon", "historico"],
        ),
    },
    "janela_plantio": {
        "funcao": janela_plantio,
        "descricao_pt_en": {
            "pt": "Calcula a janela de plantio.",
            "en": "Calculate the planting window.",
        },
        "schema": _schema(
            {**_COORDS, "cultura": {"type": "string"}, "idioma": _IDIOMA},
            ["lat", "lon", "cultura"],
        ),
    },
    "info_cultura": {
        "funcao": info_cultura,
        "descricao_pt_en": {
            "pt": "Consulta os dados de uma cultura.",
            "en": "Look up crop information.",
        },
        "schema": _schema({"nome": {"type": "string"}}, ["nome"]),
    },
    "registrar_observacao": {
        "funcao": registrar_observacao,
        "descricao_pt_en": {
            "pt": "Registra observação de campo.",
            "en": "Record a field observation.",
        },
        "schema": _schema(
            {"fazenda_id": {"type": "integer"}, "texto": {"type": "string"}},
            ["fazenda_id", "texto"],
        ),
    },
    "inscrever_alerta": {
        "funcao": inscrever_alerta,
        "descricao_pt_en": {
            "pt": "Inscreve a fazenda em alerta hídrico.",
            "en": "Subscribe a farm to water alerts.",
        },
        "schema": _schema(
            {
                "fazenda_id": {"type": "integer"},
                "cultura": {"type": "string"},
                "data_plantio": {
                    "type": "string",
                    "format": "date",
                    "description": "YYYY-MM-DD",
                },
            },
            ["fazenda_id", "cultura", "data_plantio"],
        ),
    },
}


def _resultado(valor, idioma):
    if isinstance(valor, dict):
        resultado = {k: _resultado(v, idioma) for k, v in valor.items()}
        if resultado.get("preliminar") is True:
            resultado["aviso"] = t("aviso_preliminar", idioma)
        return resultado
    if isinstance(valor, (list, tuple)):
        return [_resultado(v, idioma) for v in valor]
    return valor


def executar(nome, args):
    ferramenta = FERRAMENTAS.get(nome)
    if ferramenta is None:
        return {"erro": f"Ferramenta desconhecida: {nome}"}
    funcao = ferramenta["funcao"]
    try:
        validate(instance=args, schema=ferramenta["schema"])
    except ValidationError as erro:
        return {"erro": erro.message}
    try:
        return _resultado(funcao(**args), args.get("idioma", "pt"))
    except (ErroPontoInvalido, ErroFonteDados, ValueError) as erro:
        return {"erro": str(erro)}
