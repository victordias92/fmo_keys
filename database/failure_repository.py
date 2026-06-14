import sqlite3

from .connection import get_conn


def list_failures():
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT id, location, description, reported_by,
                   failure_date, failure_time, failure_day,
                   status, image_path, notes
            FROM failures_registry
            ORDER BY id DESC
            """
        ).fetchall()


def get_failure_by_id(failure_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT id, location, description, reported_by,
                   failure_date, failure_time, failure_day,
                   status, image_path, notes
            FROM failures_registry
            WHERE id = ?
            """,
            (failure_id,),
        ).fetchone()


def add_failure(
    location: str,
    description: str,
    reported_by: str,
    failure_date: str,
    failure_time: str,
    failure_day: str,
    notes: str = "",
) -> int:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO failures_registry (
                location, description, reported_by,
                failure_date, failure_time, failure_day,
                status, image_path, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, 'aberta', '', ?)
            """,
            (
                location.strip(),
                description.strip(),
                reported_by.strip(),
                failure_date,
                failure_time,
                failure_day,
                notes.strip(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def update_failure(
    failure_id: int,
    location: str,
    description: str,
    reported_by: str,
    failure_date: str,
    failure_time: str,
    failure_day: str,
    status: str,
    notes: str,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE failures_registry
            SET location = ?, description = ?, reported_by = ?,
                failure_date = ?, failure_time = ?, failure_day = ?,
                status = ?, notes = ?
            WHERE id = ?
            """,
            (
                location.strip(),
                description.strip(),
                reported_by.strip(),
                failure_date,
                failure_time,
                failure_day,
                status.strip(),
                notes.strip(),
                failure_id,
            ),
        )
        conn.commit()


def update_failure_image(failure_id: int, image_path: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE failures_registry SET image_path = ? WHERE id = ?",
            (image_path, failure_id),
        )
        conn.commit()


def resolve_failure(failure_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE failures_registry SET status = 'resolvida' WHERE id = ?",
            (failure_id,),
        )
        conn.commit()


def delete_failure(failure_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM failures_registry WHERE id = ?", (failure_id,))
        conn.commit()

