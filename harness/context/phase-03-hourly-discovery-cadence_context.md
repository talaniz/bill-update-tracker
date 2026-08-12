# Phase 03 Context: Hourly Discovery Cadence

## Requirements Captured

- Determine whether Congress.gov bill updates appear as a single daily batch or arrive during multiple hourly polls.
- Use the existing `poll_runs` history only; do not change polling, the Congress.gov API integration, event storage, or LLM behavior.
- Keep the existing daily update panels and add clear cadence panels to the Mothership Bill Update Tracker dashboard.
- An active weekday is a weekday with at least one successful poll that inserted updates.
- Collect 30 active weekdays before drawing an operational conclusion.

## Decisions

- Query `poll_runs.finished_at`, `poll_runs.status`, and `poll_runs.inserted_events` directly in Grafana; no schema migration or backfill is required.
- Display hourly inserted-update volume and a separate zero-or-discovery poll indicator so zero-update successes are distinguishable from missing data.
- Display the count of discovery-bearing successful polls for each active weekday to make intraday batches visible.
- Treat one discovery-bearing poll per active weekday as evidence that daily batching is likely. Multiple discovery-bearing polls on a material number of active weekdays means retain intraday LLM-summary handling.
- Grafana continues to render timestamps in the viewer's browser timezone.

## Deferred

- An automatic cadence scorecard, alert, or LLM scheduling change.
- Per-source-type counts per poll, which would require a data-model change.
