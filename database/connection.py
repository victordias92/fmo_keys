import sqlite3
from pathlib import Path
import os

# Diretório de dados do aplicativo
appdata = os.getenv("APPDATA") or os.getenv("HOME") or "/tmp"
data_dir = Path(appdata) / "KeyManager"

# cria pasta se não existir
data_dir.mkdir(parents=True, exist_ok=True)

db_path = data_dir / "keys.db"


def get_conn() -> sqlite3.Connection:
    """
    Retorna uma conexão SQLite configurada para acessar colunas por nome.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Cria a estrutura do banco caso não exista.
    """
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS keys_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT NOT NULL UNIQUE,
                last_user TEXT,
                used_date TEXT,
                used_time TEXT,
                used_day TEXT
            )
            """
        )
        conn.commit()