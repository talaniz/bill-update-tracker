from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from .collector import PollRunFailed, run_once
from .observability import log_activity
from .config import Settings


def next_run_time(settings: Settings) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.poll_interval_seconds)


def build_scheduler(settings: Settings, first_run_at: datetime | None = None) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")

    def job() -> None:
        try:
            run_once(next_run_at=next_run_time(settings))
        except PollRunFailed as exc:
            log_activity("poll_scheduler_failed", error_type=type(exc).__name__)
        except Exception as exc:
            log_activity("poll_scheduler_failed", error_type=type(exc).__name__)

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
