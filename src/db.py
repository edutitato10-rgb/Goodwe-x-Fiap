"""Acesso ao banco SQL (SQLite). O mesmo esquema roda em PostgreSQL com ajustes mínimos."""
import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")
DB_PADRAO = Path(__file__).resolve().parent.parent / "data" / "evchargeops.db"


def conectar(caminho=DB_PADRAO) -> sqlite3.Connection:
    conn = sqlite3.connect(str(caminho), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def criar_esquema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()


def definir_parametro(conn, chave: str, valor: float) -> None:
    conn.execute(
        "INSERT INTO parametro(chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (chave, valor),
    )
    conn.commit()


def obter_parametro(conn, chave: str) -> float:
    linha = conn.execute("SELECT valor FROM parametro WHERE chave = ?", (chave,)).fetchone()
    if linha is None:
        raise KeyError(f"Parâmetro não definido: {chave}")
    return float(linha["valor"])
