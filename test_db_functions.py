"""Testes automatizados das funcoes de banco (sem UI)."""
import json
import sqlite3
import tempfile
import time
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).with_name("debug-ce6eb0.log")


def dbg(hypothesis_id: str, location: str, message: str, data: dict | None = None) -> None:
    entry = {
        "sessionId": "ce6eb0",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
        "runId": "db-test",
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run_tests() -> None:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = Path(tmp.name)
    tmp.close()

    dbg("D", "test_db_functions.py:run_tests", "start", {"db": str(db_path)})

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE keys_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL UNIQUE,
            last_user TEXT, used_date TEXT, used_time TEXT, used_day TEXT
        )
        """
    )

    # add_key
    conn.execute(
        "INSERT INTO keys_registry (key_name, last_user, used_date, used_time, used_day) VALUES (?, '', '', '', '')",
        ("TEST-01",),
    )
    row = conn.execute("SELECT * FROM keys_registry WHERE key_name='TEST-01'").fetchone()
    assert row is not None
    dbg("D", "test_db_functions.py:add_key", "ok", {"id": row["id"]})

    # register_use
    now = datetime.now()
    conn.execute(
        "UPDATE keys_registry SET last_user=?, used_date=?, used_time=?, used_day=? WHERE id=?",
        ("Joao", now.strftime("%d/%m/%Y"), now.strftime("%H:%M"), "Quarta-feira", row["id"]),
    )
    row = conn.execute("SELECT * FROM keys_registry WHERE id=?", (row["id"],)).fetchone()
    assert row["last_user"] == "Joao"
    dbg("D", "test_db_functions.py:register_use", "ok", {"user": row["last_user"]})

    key_id = row["id"]
    # update_key_name
    conn.execute("UPDATE keys_registry SET key_name=? WHERE id=?", ("TEST-01-EDIT", key_id))
    row = conn.execute("SELECT key_name FROM keys_registry WHERE id=?", (key_id,)).fetchone()
    assert row["key_name"] == "TEST-01-EDIT"
    dbg("D", "test_db_functions.py:update_key_name", "ok", {"name": row["key_name"]})

    # clear_key_use
    conn.execute(
        "UPDATE keys_registry SET last_user='', used_date='', used_time='', used_day='' WHERE id=?",
        (key_id,),
    )
    row = conn.execute("SELECT * FROM keys_registry WHERE id=?", (key_id,)).fetchone()
    assert row["last_user"] == ""
    dbg("D", "test_db_functions.py:clear_key_use", "ok", {})

    # delete_key
    conn.execute("DELETE FROM keys_registry WHERE id=?", (key_id,))
    row = conn.execute("SELECT * FROM keys_registry WHERE id=?", (key_id,)).fetchone()
    assert row is None
    dbg("D", "test_db_functions.py:delete_key", "ok", {})

    # seed count
    from fmo_keys import FMO_KEYS

    inserted = 0
    for name in FMO_KEYS:
        try:
            conn.execute(
                "INSERT INTO keys_registry (key_name, last_user, used_date, used_time, used_day) VALUES (?, '', '', '', '')",
                (name,),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    total = conn.execute("SELECT COUNT(*) AS c FROM keys_registry").fetchone()["c"]
    dbg("D", "test_db_functions.py:seed_fmo", "ok", {"inserted": inserted, "total": total})

    conn.close()
    db_path.unlink(missing_ok=True)
    dbg("D", "test_db_functions.py:run_tests", "all_passed", {})


if __name__ == "__main__":
    run_tests()
    print("DB tests passed. See debug-ce6eb0.log")
