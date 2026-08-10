from collections import Counter

from .models import UpdateEvent


def rollup_events_in_memory(events: list[UpdateEvent]) -> dict[tuple[str, str], int]:
    counts: Counter[tuple[str, str]] = Counter()
    for event in events:
        counts[(event.update_date.date().isoformat(), event.source_type)] += 1
    return dict(counts)

