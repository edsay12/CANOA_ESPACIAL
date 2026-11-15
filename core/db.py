"""Banco SQLite compartilhado entre site e bot.

O caminho padrão é db.sqlite. Na primeira criação, alertas do antigo
data/fieldshift.db são copiados sem alterar o arquivo original. DB_PATH explícito
distinto seleciona somente o arquivo indicado; esquemas antigos nele são migrados.
"""

import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db.sqlite"
LEGACY_DB_PATH = ROOT / "data" / "fieldshift.db"


@contextmanager
def _conectar():
    configurado = os.environ.get("DB_PATH")
    caminho = DB_PATH if not configurado or configurado == "db.sqlite" else Path(configurado)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(caminho, timeout=30)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute("BEGIN IMMEDIATE")
            existia = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alertas'"
            ).fetchone() is not None
            conn.execute("CREATE TABLE IF NOT EXISTS fazendas (id INTEGER PRIMARY KEY, lat REAL NOT NULL, "
                         "lon REAL NOT NULL, pais TEXT, chat_id TEXT UNIQUE, criado_em TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS observacoes (id INTEGER PRIMARY KEY, "
                         "fazenda_id INTEGER NOT NULL REFERENCES fazendas(id), data TEXT NOT NULL, "
                         "texto TEXT, foto_path TEXT, descricao_ia TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS alertas (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "fazenda_id INTEGER REFERENCES fazendas(id), chat_id TEXT, lat REAL, lon REAL, "
                         "cultura TEXT NOT NULL, data_plantio TEXT NOT NULL, idioma TEXT DEFAULT 'pt', "
                         "ativo INTEGER DEFAULT 1, ultimo_envio TEXT)")
            colunas = {row[1] for row in conn.execute("PRAGMA table_info(alertas)")}
            for nome, tipo in (("fazenda_id", "INTEGER REFERENCES fazendas(id)"), ("ultimo_envio", "TEXT")):
                if nome not in colunas:
                    conn.execute(f"ALTER TABLE alertas ADD COLUMN {nome} {tipo}")
            if not existia and caminho.resolve() == DB_PATH.resolve() and LEGACY_DB_PATH.is_file():
                with closing(sqlite3.connect(LEGACY_DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)) as legado:
                    if legado.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='alertas'").fetchone():
                        rows = legado.execute("SELECT id, chat_id, lat, lon, cultura, data_plantio, idioma, ativo "
                                              "FROM alertas").fetchall()
                        conn.executemany("INSERT INTO alertas "
                                         "(id, chat_id, lat, lon, cultura, data_plantio, idioma, ativo) "
                                         "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise


def _agora():
    return datetime.now(UTC).isoformat()


def criar_fazenda(lat, lon, pais, chat_id=None):
    with _conectar() as conn:
        cur = conn.execute("INSERT INTO fazendas (lat, lon, pais, chat_id, criado_em) VALUES (?, ?, ?, ?, ?)",
                           (lat, lon, pais, str(chat_id) if chat_id is not None else None, _agora()))
        return cur.lastrowid


def fazenda(identificador):
    with _conectar() as conn:
        row = conn.execute("SELECT * FROM fazendas WHERE id = ?", (identificador,)).fetchone()
        return dict(row) if row else None


def fazenda_por_chat(chat_id):
    with _conectar() as conn:
        row = conn.execute("SELECT * FROM fazendas WHERE chat_id = ?", (str(chat_id),)).fetchone()
        return dict(row) if row else None


def vincular_chat(fazenda_id, chat_id):
    with _conectar() as conn:
        if conn.execute("SELECT 1 FROM fazendas WHERE id = ?", (fazenda_id,)).fetchone():
            conn.execute("UPDATE fazendas SET chat_id = NULL WHERE chat_id = ?", (str(chat_id),))
            conn.execute("UPDATE fazendas SET chat_id = ? WHERE id = ?", (str(chat_id), fazenda_id))


def atualizar_local(fazenda_id, lat, lon, pais):
    with _conectar() as conn:
        conn.execute("UPDATE fazendas SET lat = ?, lon = ?, pais = ? WHERE id = ?", (lat, lon, pais, fazenda_id))


def salvar_observacao(fazenda_id, texto, foto_path, descricao_ia):
    with _conectar() as conn:
        cur = conn.execute("INSERT INTO observacoes (fazenda_id, data, texto, foto_path, descricao_ia) "
                           "VALUES (?, ?, ?, ?, ?)", (fazenda_id, _agora(), texto, foto_path, descricao_ia))
        return cur.lastrowid


def listar_observacoes():
    with _conectar() as conn:
        return [dict(row) for row in conn.execute("SELECT o.*, f.lat, f.lon FROM observacoes o "
                                                   "JOIN fazendas f ON f.id = o.fazenda_id")]


def inscrever_alerta(fazenda_id, cultura, data_plantio):
    with _conectar() as conn:
        f = conn.execute("SELECT chat_id, lat, lon FROM fazendas WHERE id = ?", (fazenda_id,)).fetchone()
        if f is None:
            raise ValueError("Fazenda não encontrada")
        # Os campos legados também permitem inserir em tabelas antigas com NOT NULL.
        cur = conn.execute("INSERT INTO alertas (fazenda_id, chat_id, lat, lon, cultura, data_plantio, ativo) "
                           "VALUES (?, ?, ?, ?, ?, ?, 1)",
                           (fazenda_id, f["chat_id"] or "", f["lat"], f["lon"], cultura, data_plantio))
        return cur.lastrowid


def criar_alerta(chat_id, lat, lon, cultura, data_plantio, idioma="pt"):
    with _conectar() as conn:
        cur = conn.execute("INSERT INTO alertas (chat_id, lat, lon, cultura, data_plantio, idioma, ativo) "
                           "VALUES (?, ?, ?, ?, ?, ?, 1)",
                           (str(chat_id), float(lat), float(lon), cultura, data_plantio, idioma))
        return cur.lastrowid


def listar_alertas(ativos=True):
    with _conectar() as conn:
        filtro = "WHERE a.ativo = 1" if ativos else ""
        rows = conn.execute("SELECT a.id, a.fazenda_id, "
                            "CASE WHEN a.fazenda_id IS NULL THEN a.chat_id ELSE f.chat_id END AS chat_id, "
                            "CASE WHEN a.fazenda_id IS NULL THEN a.lat ELSE f.lat END AS lat, "
                            "CASE WHEN a.fazenda_id IS NULL THEN a.lon ELSE f.lon END AS lon, "
                            "a.cultura, a.data_plantio, a.idioma, a.ativo, a.ultimo_envio "
                            "FROM alertas a LEFT JOIN fazendas f ON f.id = a.fazenda_id " + filtro).fetchall()
        return [dict(row) for row in rows]


def desativar_alerta(alerta_id):
    with _conectar() as conn:
        conn.execute("UPDATE alertas SET ativo = 0 WHERE id = ?", (alerta_id,))


def marcar_alerta_enviado(alerta_id, quando):
    if isinstance(quando, datetime):
        quando = quando.isoformat()
    with _conectar() as conn:
        conn.execute("UPDATE alertas SET ultimo_envio = ? WHERE id = ?", (quando, alerta_id))
