from __future__ import annotations

import json
import logging


activity_logger = logging.getLogger("bill_update_tracker.activity")
if not activity_logger.handlers:
    activity_handler = logging.StreamHandler()
    activity_handler.setFormatter(logging.Formatter("%(message)s"))
    activity_logger.addHandler(activity_handler)
activity_logger.setLevel(logging.INFO)
activity_logger.propagate = False


def log_activity(event: str, **fields: object) -> None:
    """Emit metadata-only lifecycle events as one JSON object per log line."""
    activity_logger.info(json.dumps({"event": event, **fields}, default=str, sort_keys=True))
