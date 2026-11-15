import multiprocessing
import sqlite3
from contextlib import closing
from datetime import UTC, datetime

import pytest

from core import db


@pytest.fixture
def banco(tmp_path, monkeypatch):
    caminho = tmp_path / "db.sqlite"
    monkeypatch.setenv("DB_PATH", str(caminho))
    return caminho


def _gravar_em_processo(caminho, inicio, fila, grupo):
    import os

    os.environ["DB_PATH"] = str(caminho)
    inicio.wait(20)
    for i in range(15):
        db.criar_fazenda(grupo, i, "BR")
    fila.put(None)


def test_criar_fazenda_retorna_id(banco):
    identificador = db.criar_fazenda(-10.5, -45.5, "BR")
    assert isinstance(identificador, int)
    with closing(sqlite3.connect(banco)) as conn:
        assert conn.execute("SELECT lat, lon, pais FROM fazendas WHERE id = ?", (identificador,)).fetchone() == (
            -10.5, -45.5, "BR"
        )


def test_fazenda_por_chat(banco):
    identificador = db.criar_fazenda(-10.5, -45.5, "BR", chat_id=123)
    fazenda = db.fazenda_por_chat(123)
    assert {k: fazenda[k] for k in ("id", "lat", "lon", "pais")} == {
        "id": identificador, "lat": -10.5, "lon": -45.5, "pais": "BR"
    }
    assert db.fazenda_por_chat(456) is None


def test_vincular_chat(banco):
    anterior = db.criar_fazenda(1, 2, "BR", chat_id=123)
    nova = db.criar_fazenda(3, 4, "AR")
    db.vincular_chat(nova, 123)
    assert db.fazenda_por_chat(123)["id"] == nova
    assert db.fazenda(anterior)["chat_id"] is None
    db.vincular_chat(99999, 123)
    assert db.fazenda_por_chat(123)["id"] == nova


def test_salvar_e_listar_observacao(banco):
    fazenda = db.criar_fazenda(-1, -2, "BR")
    antes = datetime.now(UTC)
    identificador = db.salvar_observacao(fazenda, "folhas", "data/fotos/a.jpg", "verde")
    depois = datetime.now(UTC)
    observacao = next(o for o in db.listar_observacoes() if o["id"] == identificador)
    assert {k: observacao[k] for k in ("fazenda_id", "texto", "foto_path", "descricao_ia", "lat", "lon")} == {
        "fazenda_id": fazenda, "texto": "folhas", "foto_path": "data/fotos/a.jpg",
        "descricao_ia": "verde", "lat": -1, "lon": -2,
    }
    data = datetime.fromisoformat(observacao["data"])
    assert data.utcoffset().total_seconds() == 0
    assert antes <= data <= depois


def test_inscrever_e_listar_alerta(banco):
    fazenda = db.criar_fazenda(1, 2, "BR", chat_id=123)
    identificador = db.inscrever_alerta(fazenda, "Milho", "2026-02-15")
    alerta = next(a for a in db.listar_alertas() if a["id"] == identificador)
    assert {k: alerta[k] for k in ("fazenda_id", "cultura", "data_plantio", "ativo")} == {
        "fazenda_id": fazenda, "cultura": "Milho", "data_plantio": "2026-02-15", "ativo": 1
    }
    db.marcar_alerta_enviado(identificador, "2026-11-15T10:00:00+00:00")
    assert db.listar_alertas()[0]["ultimo_envio"] == "2026-11-15T10:00:00+00:00"
    db.desativar_alerta(identificador)
    assert db.listar_alertas() == []
    assert db.listar_alertas(ativos=False)[0]["id"] == identificador


def test_cria_tabelas_no_primeiro_uso(banco):
    assert not banco.exists()
    db.criar_fazenda(1, 2, "BR")
    assert banco.is_file()
    with closing(sqlite3.connect(banco)) as conn:
        tabelas = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"fazendas", "observacoes", "alertas"} <= tabelas


def test_dois_processos_mesmo_arquivo(banco):
    ctx = multiprocessing.get_context("spawn")
    inicio = ctx.Event()
    fila = ctx.Queue()
    processos = [ctx.Process(target=_gravar_em_processo, args=(banco, inicio, fila, grupo)) for grupo in range(2)]
    for processo in processos:
        processo.start()
    inicio.set()
    resultados = [fila.get(timeout=30) for _ in processos]
    for processo in processos:
        processo.join(30)
        assert processo.exitcode == 0
    assert resultados == [None, None]
    with closing(sqlite3.connect(banco)) as conn:
        assert set(conn.execute("SELECT lat, lon FROM fazendas")) == {
            (grupo, i) for grupo in range(2) for i in range(15)
        }
        assert conn.execute("SELECT COUNT(*) FROM fazendas").fetchone()[0] == 30


def test_dados_so_em_db_e_fotos(banco, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pasta_fotos = tmp_path / "data" / "fotos"
    pasta_fotos.mkdir(parents=True)
    foto = pasta_fotos / "1_foto.jpg"
    foto.write_bytes(b"foto")
    fazenda = db.criar_fazenda(1, 2, "BR")
    db.salvar_observacao(fazenda, "texto", str(foto), "descricao")
    assert {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()} == {
        "db.sqlite", "data/fotos/1_foto.jpg"
    }


def test_alertas_legados_migrados_e_api_preservada(banco):
    with closing(sqlite3.connect(banco)) as conn:
        conn.execute("CREATE TABLE alertas (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT NOT NULL, "
                     "lat REAL NOT NULL, lon REAL NOT NULL, cultura TEXT NOT NULL, data_plantio TEXT NOT NULL, "
                     "idioma TEXT DEFAULT 'pt', ativo INTEGER DEFAULT 1)")
        conn.execute("INSERT INTO alertas VALUES (7, '42', -1, -2, 'Soja', '2026-01-01', 'es', 1)")
        conn.execute("INSERT INTO alertas VALUES (8, '42', -3, -4, 'Milho', '2026-02-01', 'pt', 1)")
        conn.execute("INSERT INTO alertas VALUES (9, '42', -5, -6, 'Arroz', '2026-03-01', 'en', 0)")
        conn.commit()
    alerta = db.listar_alertas()[0]
    assert {k: alerta[k] for k in ("id", "chat_id", "lat", "lon", "cultura", "data_plantio", "idioma")} == {
        "id": 7, "chat_id": "42", "lat": -1, "lon": -2, "cultura": "Soja",
        "data_plantio": "2026-01-01", "idioma": "es"
    }
    assert [(a["id"], a["lat"], a["lon"], a["ativo"]) for a in db.listar_alertas(ativos=False)] == [
        (7, -1, -2, 1), (8, -3, -4, 1), (9, -5, -6, 0)
    ]
    novo = db.criar_alerta(43, 3, 4, "Milho", "2026-02-01", "en")
    assert next(a for a in db.listar_alertas() if a["id"] == novo)["chat_id"] == "43"
    db.desativar_alerta(7)
    assert [a["id"] for a in db.listar_alertas()] == [8, novo]
    banco.rename(banco.with_suffix(".moved"))


def test_importa_arquivo_legado_padrao_sem_altera_lo(tmp_path, monkeypatch):
    legado = tmp_path / "data" / "fieldshift.db"
    legado.parent.mkdir()
    with closing(sqlite3.connect(legado)) as conn:
        conn.execute("CREATE TABLE alertas (id INTEGER PRIMARY KEY, chat_id TEXT, lat REAL, lon REAL, "
                     "cultura TEXT, data_plantio TEXT, idioma TEXT, ativo INTEGER)")
        conn.execute("INSERT INTO alertas VALUES (4, '99', 1, 2, 'Soja', '2026-01-01', 'pt', 0)")
        conn.commit()
    antes = legado.read_bytes()
    monkeypatch.setenv("DB_PATH", "db.sqlite")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "db.sqlite")
    monkeypatch.setattr(db, "LEGACY_DB_PATH", legado)
    assert db.listar_alertas() == []
    assert db.listar_alertas(ativos=False)[0]["id"] == 4
    assert legado.read_bytes() == antes
    assert len(db.listar_alertas(ativos=False)) == 1
    configurado = tmp_path / "outro.sqlite"
    monkeypatch.setenv("DB_PATH", str(configurado))
    assert db.listar_alertas(ativos=False) == []
    assert configurado.is_file()
    assert legado.read_bytes() == antes
