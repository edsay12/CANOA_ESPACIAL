import copy
import json

import pytest

from bot_logica import ferramentas
from core import clima, contexto, culturas, db, modelo
from core.erros import ErroFonteDados, ErroPontoInvalido


def test_resultado_do_motor_com_fontes(monkeypatch, tmp_path):
    saida = {"fontes": ["NASA POWER", "solo"], "valor": 3, "objeto": {"dado": 9}}
    chamadas = []

    def fake(nome):
        def executar(**kwargs):
            chamadas.append((nome, kwargs))
            return copy.deepcopy(saida)

        return executar

    casos = [
        (contexto, "contexto", {"lat": -12.0, "lon": -44.0}),
        (clima, "clima_mudou", {"lat": -12.0, "lon": -44.0, "idioma": "en"}),
        (
            modelo,
            "ranking_safra",
            {"lat": -12.0, "lon": -44.0, "data_semeadura": "02-15", "idioma": "es"},
        ),
        (
            modelo,
            "planos_rotacao",
            {"lat": -12.0, "lon": -44.0, "historico": ["Soja", "Milho", "Soja"]},
        ),
        (clima, "janela_plantio", {"lat": -12.0, "lon": -44.0, "cultura": "Soja"}),
    ]
    for modulo, nome, args in casos:
        monkeypatch.setattr(modulo, nome, fake(nome))
        resultado = ferramentas.executar(nome, args)
        assert resultado == saida
        assert (
            json.loads(json.dumps(resultado, ensure_ascii=False, allow_nan=False))
            == saida
        )
        esperado = dict(args)
        if nome == "ranking_safra":
            esperado["prioridades"] = None
        if nome == "planos_rotacao":
            esperado.update(prioridades=None, idioma="pt", data_semeadura=None)
        assert chamadas[-1] == (nome, esperado)
    monkeypatch.setenv("DB_PATH", str(tmp_path / "db.sqlite"))
    fazenda = db.criar_fazenda(-12, -44, "BR", chat_id=123)
    obs = ferramentas.executar(
        "registrar_observacao", {"fazenda_id": fazenda, "texto": "folha verde"}
    )
    assert db.listar_observacoes()[0]["id"] == obs["id"]
    assert db.listar_observacoes()[0]["texto"] == "folha verde"
    assert db.listar_observacoes()[0]["foto_path"] is None
    alerta = ferramentas.executar(
        "inscrever_alerta",
        {"fazenda_id": fazenda, "cultura": "Soja", "data_plantio": "2026-02-15"},
    )
    assert db.listar_alertas()[0]["id"] == alerta["id"]
    assert db.listar_alertas()[0]["data_plantio"] == "2026-02-15"
    assert (
        ferramentas.executar("info_cultura", {"nome": "Soja"})["papel"]
        == culturas.carregar()["Soja"]["papel"]
    )


def test_erros_legiveis_sem_stacktrace(monkeypatch, tmp_path):
    for tipo in (ErroPontoInvalido, ErroFonteDados, ValueError):

        def falha(erro=tipo, **kwargs):
            raise erro("problema verificável")

        monkeypatch.setattr(contexto, "contexto", falha)
        assert ferramentas.executar("contexto", {"lat": 1, "lon": 2}) == {
            "erro": "problema verificável"
        }
    assert "erro" in ferramentas.executar("contexto", {"lat": 1})
    assert "erro" in ferramentas.executar("contexto", {"lat": 1, "lon": 2, "outro": 3})

    def bug(**kwargs):
        raise TypeError("bug interno")

    monkeypatch.setattr(contexto, "contexto", bug)
    with pytest.raises(TypeError, match="bug interno"):
        ferramentas.executar("contexto", {"lat": 1, "lon": 2})
    monkeypatch.setenv("DB_PATH", str(tmp_path / "db.sqlite"))
    fazenda = db.criar_fazenda(1, 2, "BR")
    for cultura, data in [
        ("inexistente", "2026-01-01"),
        ("Soja", "15/02/2026"),
        ("Soja", "2026-02-30"),
    ]:
        resposta = ferramentas.executar(
            "inscrever_alerta",
            {"fazenda_id": fazenda, "cultura": cultura, "data_plantio": data},
        )
        assert "erro" in resposta
    assert db.listar_alertas() == []
    assert "erro" in ferramentas.executar(
        "registrar_observacao",
        {"fazenda_id": fazenda, "texto": "x", "foto_path": "arbitrario"},
    )
    assert "erro" in ferramentas.executar(
        "registrar_observacao", {"fazenda_id": 999999, "texto": "x"}
    )
    assert db.listar_observacoes() == []
    assert "erro" in ferramentas.executar(
        "planos_rotacao", {"lat": 1, "lon": 2, "historico": [[]]}
    )
    assert "erro" in ferramentas.executar(
        "ranking_safra",
        {"lat": 1, "lon": 2, "data_semeadura": "02-15", "prioridades": {"solo": None}},
    )


def test_info_cultura():
    resultado = ferramentas.executar("info_cultura", {"nome": "Soja"})
    origem = culturas.carregar()["Soja"]
    for campo in (
        "papel",
        "familia",
        "fixa_n",
        "climas",
        "tolerancia_seca",
        "efeito_solo",
        "fonte",
    ):
        assert resultado[campo] == origem[campo]
    json.dumps(resultado, ensure_ascii=False, allow_nan=False)


def test_info_cultura_desconhecida():
    resposta = ferramentas.executar("info_cultura", {"nome": "nao existe"})
    assert "erro" in resposta
    assert all(nome in resposta["erro"] for nome in culturas.carregar())


def test_aviso_preliminar(monkeypatch):
    avisos = {
        "pt": "parâmetros genéricos da FAO, não calibrados para a região",
        "en": "generic FAO parameters, not calibrated for the region",
        "es": "parámetros genéricos de la FAO, no calibrados para la región",
    }
    original = {
        "fontes": ["NASA"],
        "itens": [{"preliminar": False}, {"detalhe": [{"preliminar": True, "n": 4}]}],
    }
    monkeypatch.setattr(clima, "clima_mudou", lambda **kwargs: original)
    for idioma, texto in avisos.items():
        resposta = ferramentas.executar(
            "clima_mudou", {"lat": 1, "lon": 2, "idioma": idioma}
        )
        assert resposta["itens"][0] == {"preliminar": False}
        assert resposta["itens"][1]["detalhe"][0]["aviso"] == texto
        assert resposta["fontes"] == ["NASA"]
        assert (
            json.loads(json.dumps(resposta, allow_nan=False))["itens"][1]["detalhe"][0][
                "n"
            ]
            == 4
        )
        monkeypatch.setattr(
            clima,
            "janela_plantio",
            lambda **kwargs: {"preliminar": True, "fontes": ["NASA"]},
        )
        janela = ferramentas.executar(
            "janela_plantio", {"lat": 1, "lon": 2, "cultura": "Soja", "idioma": idioma}
        )
        assert janela["aviso"] == texto and janela["fontes"] == ["NASA"]
        monkeypatch.setattr(
            modelo,
            "ranking_safra",
            lambda **kwargs: {"itens": [{"preliminar": True}], "fontes": ["NASA"]},
        )
        ranking = ferramentas.executar(
            "ranking_safra",
            {"lat": 1, "lon": 2, "data_semeadura": "02-15", "idioma": idioma},
        )
        assert ranking["itens"][0]["aviso"] == texto and ranking["fontes"] == ["NASA"]
    assert "aviso" not in original["itens"][1]["detalhe"][0]


def test_schemas_das_oito_ferramentas():
    nomes = {
        "contexto",
        "clima_mudou",
        "ranking_safra",
        "planos_rotacao",
        "janela_plantio",
        "info_cultura",
        "registrar_observacao",
        "inscrever_alerta",
    }
    assert set(ferramentas.FERRAMENTAS) == nomes
    for ferramenta in ferramentas.FERRAMENTAS.values():
        assert callable(ferramenta["funcao"])
        assert (
            ferramenta["descricao_pt_en"]["pt"] and ferramenta["descricao_pt_en"]["en"]
        )
        schema = ferramenta["schema"]
        assert schema["type"] == "object" and isinstance(schema["properties"], dict)
        assert set(schema["required"]) <= set(schema["properties"])
        json.dumps(schema)
    assert (
        "foto_path"
        not in ferramentas.FERRAMENTAS["registrar_observacao"]["schema"]["properties"]
    )
