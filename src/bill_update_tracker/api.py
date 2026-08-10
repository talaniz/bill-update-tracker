from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .db import connect, get_status, init_db, set_next_run_at
from .scheduler import build_scheduler, next_run_time


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.database_url)
    scheduler = None
    if settings.enable_scheduler:
        scheduled_at = next_run_time(settings)
        with connect(settings.database_url) as connection:
            set_next_run_at(connection, scheduled_at)
            connection.commit()
        scheduler = build_scheduler(settings, first_run_at=scheduled_at)
        scheduler.start()
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)


app = FastAPI(title="Bill Update Tracker", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
def status() -> dict:
    settings = get_settings()
    with connect(settings.database_url) as connection:
        return get_status(connection)
