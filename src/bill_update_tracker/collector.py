from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from .config import get_settings
from .congress_gateway import CongressGateway
from .db import connect, finish_poll_run, init_db, insert_events, refresh_rollups, start_poll_run
from .normalize import normalize_bill_action, normalize_summary, normalize_text_version
from .windows import collection_window_start


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

    with connect(settings.database_url) as connection:
        run_id = start_poll_run(connection, resolved_next_run_at)
        connection.commit()
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
                    error=str(exc),
                )
                failure_connection.commit()
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run-once", "init-db"])
    args = parser.parse_args()

    settings = get_settings()
    if args.command == "init-db":
        init_db(settings.database_url)
        print("database initialized")
        return 0

    inserted = run_once()
    print(f"inserted_events={inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
