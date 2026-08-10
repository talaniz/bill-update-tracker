from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


BILL_ACTION_UPDATE = "bill_latest_action"
BILL_TEXT_UPDATE = "bill_text_version"
BILL_SUMMARY_UPDATE = "bill_summary"


@dataclass(frozen=True)
class UpdateEvent:
    event_key: str
    source_type: str
    update_date: datetime
    bill_congress: int | None = None
    bill_type: str | None = None
    bill_number: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

