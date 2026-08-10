from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import BILL_ACTION_UPDATE, BILL_SUMMARY_UPDATE, BILL_TEXT_UPDATE, UpdateEvent


def parse_congress_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def bill_identity(item: dict[str, Any]) -> tuple[int | None, str | None, str | None]:
    congress = item.get("congress")
    bill_type = item.get("type") or item.get("billType")
    number = item.get("number") or item.get("billNumber")
    return (
        int(congress) if congress is not None else None,
        str(bill_type).lower() if bill_type is not None else None,
        str(number) if number is not None else None,
    )


def normalize_bill_action(item: dict[str, Any]) -> UpdateEvent | None:
    latest_action = item.get("latestAction") or {}
    update_value = item.get("updateDate") or latest_action.get("actionDate")
    if not update_value:
        return None
    congress, bill_type, number = bill_identity(item)
    update_date = parse_congress_datetime(update_value)
    action_text = latest_action.get("text") or latest_action.get("actionCode") or "latest-action"
    event_key = f"{BILL_ACTION_UPDATE}:{congress}:{bill_type}:{number}:{update_date.isoformat()}:{action_text}"
    return UpdateEvent(
        event_key=event_key,
        source_type=BILL_ACTION_UPDATE,
        bill_congress=congress,
        bill_type=bill_type,
        bill_number=number,
        update_date=update_date,
        payload=item,
    )


def normalize_text_version(item: dict[str, Any]) -> UpdateEvent | None:
    update_value = item.get("date") or item.get("updateDate") or item.get("lastUpdateDate")
    if not update_value:
        return None
    congress, bill_type, number = bill_identity(item)
    update_date = parse_congress_datetime(update_value)
    version_code = item.get("type") or item.get("versionCode") or item.get("formats", {}).get("type")
    event_key = f"{BILL_TEXT_UPDATE}:{congress}:{bill_type}:{number}:{version_code}:{update_date.isoformat()}"
    return UpdateEvent(
        event_key=event_key,
        source_type=BILL_TEXT_UPDATE,
        bill_congress=congress,
        bill_type=bill_type,
        bill_number=number,
        update_date=update_date,
        payload=item,
    )


def normalize_summary(item: dict[str, Any]) -> UpdateEvent | None:
    update_value = item.get("updateDate")
    if not update_value:
        return None
    congress, bill_type, number = bill_identity(item)
    update_date = parse_congress_datetime(update_value)
    version_code = item.get("versionCode") or item.get("actionDesc") or "summary"
    event_key = f"{BILL_SUMMARY_UPDATE}:{congress}:{bill_type}:{number}:{version_code}:{update_date.isoformat()}"
    return UpdateEvent(
        event_key=event_key,
        source_type=BILL_SUMMARY_UPDATE,
        bill_congress=congress,
        bill_type=bill_type,
        bill_number=number,
        update_date=update_date,
        payload=item,
    )
