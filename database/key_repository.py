
from .connection import get_conn
from fmo_keys import FMO_KEYS
import sqlite3



def seed_fmo_keys() -> int:
    """Insere chaves do claviculario FMO que ainda nao existem."""
    inserted = 0
    with get_conn() as conn:
        for name in FMO_KEYS:
            try:
                conn.execute(
                    """
                    INSERT INTO keys_registry (key_name, last_user, used_date, used_time, used_day)
                    VALUES (?, '', '', '', '')
                    """,
                    (name,),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                continue
    return inserted


def update_key_use(
    key_id: int,
    user: str,
    used_date: str,
    used_time: str,
    used_day: str,) -> None:

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE keys_registry
            SET last_user = ?,
                used_date = ?,
                used_time = ?,
                used_day = ?
            WHERE id = ?
            """,
            (
                user,
                used_date,
                used_time,
                used_day,
                key_id,
            ),
        )
        conn.commit()

def get_key_by_id(key_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT id, key_name, last_user, used_date, used_time, used_day
            FROM keys_registry
            WHERE id = ?
            """,
            (key_id,),
        ).fetchone()

def clear_key_use(key_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE keys_registry
            SET last_user = '', used_date = '', used_time = '', used_day = ''
            WHERE id = ?
            """,
            (key_id,),
        )
    


def add_key(name: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO keys_registry (key_name, last_user, used_date, used_time, used_day)
            VALUES (?, '', '', '', '')
            """,
            (name.strip(),),
        )



def list_keys(): 
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, key_name, last_user, used_date, used_time, used_day
            FROM keys_registry
            ORDER BY key_name
        """
    ).fetchall()
    return rows




def update_key_name(key_id: int, new_name: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE keys_registry
            SET key_name = ?
            WHERE id = ?
            """,
            (new_name.strip(), key_id),
        )


def delete_key(key_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM keys_registry WHERE id = ?", (key_id,))


