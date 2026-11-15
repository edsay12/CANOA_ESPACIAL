"""Banco SQLite compartilhado entre site e bot: fazendas, observacoes, alertas."""
"""Persistência SQLite para inscrições de alertas hídricos do bot."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fieldshift.db"


def _conectar():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            cultura TEXT NOT NULL,
            data_plantio TEXT NOT NULL,
            idioma TEXT DEFAULT 'pt',
            ativo INTEGER DEFAULT 1
        )
        """
    )
    conn.commit()
    return conn


def criar_alerta(chat_id: str | int, lat: float, lon: float, cultura: str, data_plantio: str, idioma: str = "pt") -> int:
    """Registra uma lavoura para monitoramento diário (data_plantio no formato YYYY-MM-DD)."""
    with _conectar() as conn:
        cur = conn.execute(
            "INSERT INTO alertas (chat_id, lat, lon, cultura, data_plantio, idioma, ativo) VALUES (?, ?, ?, ?, ?, ?, 1)",
            (str(chat_id), float(lat), float(lon), cultura, data_plantio, idioma),
        )
        conn.commit()
        return cur.lastrowid


def listar_alertas() -> list[dict]:
    """Retorna todas as inscrições ativas no formato dict."""
    with _conectar() as conn:
        rows = conn.execute("SELECT * FROM alertas WHERE ativo = 1").fetchall()
        return [dict(r) for r in rows]


def desativar_alerta(alerta_id: int) -> None:
    with _conectar() as conn:
        conn.execute("UPDATE alertas SET ativo = 0 WHERE id = ?", (alerta_id,))
        conn.commit()