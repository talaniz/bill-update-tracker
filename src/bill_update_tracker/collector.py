from __future__ import annotations

import argparse
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

from .config import get_settings
from .congress_gateway import CongressGateway
from .db import connect, finish_poll_run, init_db, insert_events, refresh_rollups, start_poll_run
from .normalize import normalize_bill_action, normalize_summary, normalize_text_version
from .observability import log_activity
from .windows import collection_window_start


class PollRunFailed(RuntimeError):
    """A safe failure boundary for scheduler and CLI callers."""

    def __init__(self, error_type: str) -> None:
        super().__init__(f"poll_failed error_type={error_type}")


def collect_events(gateway: CongressGateway, since: datetime):
    payload = gateway.fetch_updates_since(since)
    events = []
    for item in payload.get("bill_actions", []):
        event = normalize_bill_action(item)
        if event:
            events.append(event)
    for item in payload.get("summaries", []):
        event = normalize_summary(item)
        if event:
            events.append(event)
    for item in payload.get("text_versions", []):
        event = normalize_text_version(item)
        if event:
            events.append(event)
    return events


def run_once(next_run_at: datetime | None = None) -> int:
    settings = get_settings()
    init_db(settings.database_url)
    since = collection_window_start(settings.tracker_timezone, settings.initial_lookback_days)
    resolved_next_run_at = next_run_at or (
        datetime.now(timezone.utc) + timedelta(seconds=settings.poll_interval_seconds)
    )

    started_at = time.monotonic()
    with connect(settings.database_url) as connection:
        run_id = start_poll_run(connection, resolved_next_run_at)
        connection.commit()
        log_activity(
            "poll_started",
            run_id=run_id,
            since=since.isoformat(),
            next_run_at=resolved_next_run_at.isoformat(),
        )
        try:
            gateway = CongressGateway(
                settings.resolved_congress_api_key() or "",
                target_congress=settings.resolved_target_congress(),
                track_current_congress_only=settings.track_current_congress_only,
            )
            events = collect_events(gateway, since)
            inserted = insert_events(connection, events)
            refresh_rollups(connection)
            finish_poll_run(connection, run_id, "success", inserted, resolved_next_run_at)
            connection.commit()
            log_activity(
                "poll_succeeded",
                run_id=run_id,
                duration_ms=round((time.monotonic() - started_at) * 1000),
                observed_events=len(events),
                inserted_events=inserted,
                event_counts=dict(Counter(event.source_type for event in events)),
            )
            return inserted
        except Exception as exc:
            connection.rollback()
            with connect(settings.database_url) as failure_connection:
                finish_poll_run(
                    failure_connection,
                    run_id,
                    "failed",
                    0,
                    resolved_next_run_at,
                    error=type(exc).__name__,
                )
                failure_connection.commit()
            log_activity(
                "poll_failed",
                run_id=run_id,
                duration_ms=round((time.monotonic() - started_at) * 1000),
                error_type=type(exc).__name__,
            )
            raise PollRunFailed(type(exc).__name__) from None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run-once", "init-db"])
    args = parser.parse_args()

    settings = get_settings()
    if args.command == "init-db":
        init_db(settings.database_url)
        print("database initialized")
        return 0

    try:
        inserted = run_once()
    except Exception as exc:
        log_activity("poll_cli_failed", error_type=type(exc).__name__)
        return 1
    print(f"inserted_events={inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
