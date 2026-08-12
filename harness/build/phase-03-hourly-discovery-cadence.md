# Phase 03: Hourly Discovery Cadence

## Objective

Make the tracker dashboard show when successful hourly polls actually discover new bill updates, so the team can gather evidence for an eventual LLM-summary cadence decision.

## Context Inputs

- `harness/context/phase-03-hourly-discovery-cadence_context.md`
- `AGENTS.md`
- `harness/build/phase-02-mothership-observability.md`

## Build Instructions

1. Preserve the existing daily update and scheduler-status panels.
2. Add an hourly time-series panel that sums `inserted_events` for successful, completed polls.
3. Add an hourly indicator that returns zero for a successful poll with no discoveries and one when at least one update was discovered.
4. Add a weekday-only active-day panel that counts successful discovery-bearing polls per day.
5. Describe the 30-active-weekday evidence rule in the dashboard panel descriptions.

## Acceptance Criteria

- The dashboard distinguishes successful zero-update polls from polls that discover updates.
- Existing poll history renders without a database migration or API call.
- The active-day panel excludes weekends and includes only weekdays with discoveries.
- Dashboard timestamps render in the browser timezone and all queries honor the selected Grafana time range.

## Test Plan

- Add JSON-level dashboard tests for all three cadence panels, their successful-poll filtering, and the active-day rule.
- Run Python tests, dashboard JSON validation, Compose rendering, Ansible syntax validation, harness validation, and `git diff --check`.
- On the Pi, verify historical poll data renders and a future hourly poll appears without changing the scheduler.

## GitHub Gate

Commit, push, deployment, and PR creation require explicit human approval.
