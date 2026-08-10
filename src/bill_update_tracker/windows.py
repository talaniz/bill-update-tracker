from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def collection_window_start(tracker_timezone: str, initial_lookback_days: int = 0) -> datetime:
    tracker_tz = ZoneInfo(tracker_timezone)
    local_midnight = datetime.now(tracker_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    if initial_lookback_days > 0:
        local_midnight = local_midnight - timedelta(days=initial_lookback_days)
    return local_midnight.astimezone(timezone.utc)

