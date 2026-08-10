from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from .collector import run_once
from .config import Settings


def next_run_time(settings: Settings) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.poll_interval_seconds)


def build_scheduler(settings: Settings, first_run_at: datetime | None = None) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")

    def job() -> None:
        run_once(next_run_at=next_run_time(settings))

    scheduler.add_job(
        job,
        "interval",
        seconds=settings.poll_interval_seconds,
        id="congress-poll",
        next_run_time=first_run_at or next_run_time(settings),
        replace_existing=True,
        max_instances=1,
    )
    return scheduler
