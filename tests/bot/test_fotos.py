from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from bot_logica.fotos import Fotos, VisaoGroq, maior_foto
from bot_logica.idioma import t
from core import db
from core.erros import ErroFonteDados

AGORA = datetime(2026, 11, 15, 12, 30, 40, 123456, tzinfo=UTC)


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "db.sqlite"))
    fazenda = db.criar_fazenda(-12, -45, "BR", 123)
    pasta = tmp_path / "data" / "fotos"
    visao = lambda conteudo, idioma: "Folhas verdes e solo exposto."
    alertas = SimpleNamespace(
        situacao=lambda *args: {"ks": 0.42, "dias_ate_meio": 3, "alerta": True}
    )
    return Fotos(db, visao, alertas, pasta_fotos=pasta), fazenda, pasta, alertas


def test_salva_maior_foto(ambiente):
    fotos, fazenda, pasta, _ = ambiente
    variantes = [
        SimpleNamespace(width=100, height=100, conteudo=b"pequena"),
        SimpleNamespace(width=200, height=300, conteudo=b"maior"),
        SimpleNamespace(width=250, height=200, conteudo=b"media"),
    ]
    selecionada = maior_foto(variantes)
    assert selecionada is variantes[1]
    fotos.tratar_foto(123, selecionada.conteudo, "legenda", "pt", AGORA)
    arquivo = next(pasta.glob("*.jpg"))
    assert arquivo.name == f"{fazenda}_20261115_123040_123456.jpg"
    assert arquivo.read_bytes() == b"maior"
    fotos.tratar_foto(123, b"outra", None, "pt", AGORA)
    assert sorted(p.read_bytes() for p in pasta.glob("*.jpg")) == [b"maior", b"outra"]


def test_descricao_sem_diagnostico(ambiente):
    fotos, _, pasta, _ = ambiente
    eventos = []

    def descrever(conteudo, idioma):
        assert len(list(pasta.glob("*.jpg"))) == 1
        eventos.append((conteudo, idioma))
        return "Folhas verdes"

    fotos.descrever = descrever
    fotos.tratar_foto(123, b"jpeg", "", "es", AGORA)
    assert eventos == [(b"jpeg", "es")]

    class Cliente:
        def __init__(self):
            self.chat = SimpleNamespace(completions=self)
            self.opcoes = None
            self.chamada = None

        def with_options(self, **kw):
            self.opcoes = kw
            return self

        def create(self, **kw):
            self.chamada = kw
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(message=SimpleNamespace(content="Cultivo verde"))
                ]
            )

    cliente = Cliente()
    visao = VisaoGroq(cliente, "visao-modelo")
    assert visao(b"jpeg", "es") == "Cultivo verde"
    assert cliente.opcoes["base_url"] == "https://api.groq.com/openai/v1"
    chamada = cliente.chamada
    assert chamada["model"] == "visao-modelo" and chamada["timeout"] == 30
    partes = chamada["messages"][0]["content"]
    instrucoes = partes[0]["text"].lower()
    assert all(x in instrucoes for x in ("cultura", "cor", "murch", "solo"))
    assert "responda no idioma es" in instrucoes
    assert "não faça diagnóstico nem atribua causas" in instrucoes
    assert partes[1]["image_url"]["url"] == "data:image/jpeg;base64,anBlZw=="


def test_registra_observacao(ambiente):
    fotos, fazenda, pasta, _ = ambiente
    fotos.tratar_foto(123, b"a", "Folhas amarelas", "pt", AGORA)
    fotos.tratar_foto(123, b"b", None, "pt", AGORA)
    observacoes = db.listar_observacoes()
    assert [o["texto"] for o in observacoes] == ["Folhas amarelas", ""]
    assert all(
        o["fazenda_id"] == fazenda
        and o["descricao_ia"] == "Folhas verdes e solo exposto."
        for o in observacoes
    )
    assert {Path(o["foto_path"]) for o in observacoes} == set(pasta.glob("*.jpg"))


def test_situacao_hidrica_com_alerta(ambiente):
    fotos, fazenda, _, alertas = ambiente
    outro = db.criar_fazenda(3, 4, "BR", 456)
    db.inscrever_alerta(fazenda, "Soja", "2026-10-01")
    db.inscrever_alerta(outro, "Milho", "2026-10-02")
    chamadas = []
    alertas.situacao = lambda *args: (
        chamadas.append(args) or {"ks": 0.42, "dias_ate_meio": 3, "alerta": True}
    )
    resposta = fotos.tratar_foto(123, b"a", None, "pt", AGORA)
    assert chamadas == [(-12.0, -45.0, "Soja", "2026-10-01", AGORA)]
    assert "Soja" in "".join(resposta) and "0.42" in "".join(resposta)
    assert db.listar_alertas()[0]["ultimo_envio"] is None
    alertas.situacao = lambda *args: (_ for _ in ()).throw(ErroFonteDados("offline"))
    resposta = fotos.tratar_foto(123, b"b", "", "pt", AGORA)
    assert "Folhas verdes" in "".join(resposta)
    assert len(db.listar_observacoes()) == 2


def test_termina_com_confirme_no_campo(ambiente):
    fotos, _, _, _ = ambiente
    fotos.descrever = lambda *args: "x" * 4090
    for lang in ("pt", "en", "es"):
        resposta = fotos.tratar_foto(123, b"a", None, lang, AGORA)
        assert all(len(texto) <= 4096 for texto in resposta)
        assert resposta[-1].endswith(t("confirme_campo", lang))


def test_foto_sem_fazenda(ambiente):
    fotos, _, pasta, _ = ambiente
    fotos.descrever = lambda *args: pytest.fail("não deve chamar visão")
    resposta = fotos.tratar_foto(999, b"a", None, "pt", AGORA)
    assert t("pedir_localizacao", "pt") in "".join(resposta)
    assert resposta[-1].endswith(t("confirme_campo", "pt"))
    assert not pasta.exists() and db.listar_observacoes() == []


def test_falha_de_visao_ou_persistencia_limpa_apenas_arquivo_da_tentativa(
    ambiente, monkeypatch
):
    fotos, _, pasta, _ = ambiente
    fotos.tratar_foto(123, b"preservada", None, "pt", AGORA)
    original = next(pasta.glob("*.jpg"))

    def falha(*args):
        raise RuntimeError("segredo")

    fotos.descrever = falha
    resposta = fotos.tratar_foto(123, b"remover", None, "pt", AGORA)
    assert "segredo" not in "".join(resposta) and resposta[-1].endswith(
        t("confirme_campo", "pt")
    )
    assert (
        list(pasta.glob("*.jpg")) == [original]
        and original.read_bytes() == b"preservada"
    )
    fotos.descrever = lambda *args: "descrição"
    monkeypatch.setattr(db, "salvar_observacao", falha)
    fotos.tratar_foto(123, b"remover", None, "pt", AGORA)
    assert list(pasta.glob("*.jpg")) == [original]


def test_situacao_inclui_legado_da_mesma_area(ambiente):
    fotos, _, _, alertas = ambiente
    db.criar_alerta(123, -12, -45, "Soja", "2026-10-01")
    db.criar_alerta(123, -11, -45, "Milho", "2026-10-01")
    chamadas = []
    alertas.situacao = lambda *args: chamadas.append(args) or {"ks": 0.9}
    resposta = fotos.tratar_foto(123, b"foto", None, "pt", AGORA)
    assert [a[2] for a in chamadas] == ["Soja"]
    assert "Soja" in "".join(resposta) and "Milho" not in "".join(resposta)
