from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from .models import UpdateEvent


def schema_path() -> Path:
    candidates = []
    if os.environ.get("SCHEMA_PATH"):
        candidates.append(Path(os.environ["SCHEMA_PATH"]))
    candidates.extend(
        [
            Path.cwd() / "sql" / "001_init.sql",
            Path(__file__).resolve().parents[2] / "sql" / "001_init.sql",
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not find sql/001_init.sql")


@contextmanager
def connect(database_url: str) -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        yield connection


def init_db(database_url: str) -> None:
    with connect(database_url) as connection:
        connection.execute(schema_path().read_text())
        connection.commit()


def insert_events(connection: psycopg.Connection, events: list[UpdateEvent]) -> int:
    inserted = 0
    for event in events:
        result = connection.execute(
            """
            INSERT INTO update_events (
                event_key,
                source_type,
                bill_congress,
                bill_type,
                bill_number,
                update_date,
                payload
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (event_key) DO NOTHING
            RETURNING id
            """,
            (
                event.event_key,
                event.source_type,
                event.bill_congress,
                event.bill_type,
                event.bill_number,
                event.update_date,
                json.dumps(event.payload),
            ),
        ).fetchone()
        if result:
            inserted += 1
    return inserted


def refresh_rollups(connection: psycopg.Connection) -> None:
    connection.execute(
        """
        INSERT INTO daily_update_rollups (day, source_type, update_count, updated_at)
        SELECT update_date::date AS day, source_type, COUNT(*)::integer AS update_count, now()
        FROM update_events
        GROUP BY update_date::date, source_type
        ON CONFLICT (day, source_type)
        DO UPDATE SET update_count = EXCLUDED.update_count, updated_at = now()
        """
    )


def start_poll_run(connection: psycopg.Connection, next_run_at: datetime | None) -> int:
    row = connection.execute(
        """
        INSERT INTO poll_runs (status, next_run_at)
        VALUES ('running', %s)
        RETURNING id
        """,
        (next_run_at,),
    ).fetchone()
    connection.execute(
        """
        UPDATE scheduler_state
        SET is_running = true,
            last_started_at = now(),
            last_status = 'running',
            next_run_at = %s,
            updated_at = now()
        WHERE id = 1
        """,
        (next_run_at,),
    )
    return int(row["id"])


def finish_poll_run(
    connection: psycopg.Connection,
    run_id: int,
    status: str,
    inserted_events: int,
    next_run_at: datetime | None,
    error: str | None = None,
) -> None:
    connection.execute(
        """
        UPDATE poll_runs
        SET status = %s,
            inserted_events = %s,
            error = %s,
            next_run_at = %s,
            finished_at = now()
        WHERE id = %s
        """,
        (status, inserted_events, error, next_run_at, run_id),
    )
    connection.execute(
        """
        UPDATE scheduler_state
        SET is_running = false,
            last_finished_at = now(),
            last_status = %s,
            last_inserted_events = %s,
            next_run_at = %s,
            updated_at = now()
        WHERE id = 1
        """,
        (status, inserted_events, next_run_at),
    )


def get_status(connection: psycopg.Connection) -> dict:
    row = connection.execute("SELECT * FROM scheduler_state WHERE id = 1").fetchone()
    return dict(row) if row else {}


def set_next_run_at(connection: psycopg.Connection, next_run_at: datetime) -> None:
    connection.execute(
        """
        UPDATE scheduler_state
        SET next_run_at = %s,
            updated_at = now()
        WHERE id = 1
        """,
        (next_run_at,),
    )
