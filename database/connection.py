import sqlite3
from pathlib import Path
import os

# Diretório de dados do aplicativo
data_dir = Path(os.getenv("APPDATA")) / "KeyManager"
data_dir.mkdir(parents=True, exist_ok=True)

# Arquivo do banco SQLite
DB_PATH = data_dir / "keys.db"


def get_conn() -> sqlite3.Connection:
    """
    Retorna uma conexão SQLite configurada para acessar colunas por nome.
    """
    conn = sqlite3.connect(DB_PATH)
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