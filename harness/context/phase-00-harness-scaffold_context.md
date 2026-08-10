# Phase 00 Context

## Requirements Captured

- Count bill-related updates per day.
- Track total updates and break down by update type.
- Update types for the MVP: bill latest action, bill text version, and official summary.
- Poll hourly and roll up daily.
- Display last query, next scheduled query, and running state in Grafana.
- Use FastAPI for the lightweight tracker service.
- Use Docker Compose with Postgres and Grafana for laptop and Raspberry Pi deployment.
- Use `talaniz/congress.py` for Congress.gov access.
- Do not leak `CONGRESS_API_KEY`; the user's local source is `~/.zshrc.secrets`.
- Initial tracking starts from the current day only.
- The tracker defaults to the current Congress reported by Congress.gov because all-congress bill pagination returned API 500 errors during live validation on 2026-08-10.

## Decisions

- Store raw update events with a deterministic `event_key` so repeated polls are idempotent.
- Store daily rollups in Postgres so Grafana can query historical counts directly.
- Use fixture-backed tests rather than live API tests in the default verification flow.

## Deferred

- Exact LLM-call strategy will be determined after observing update volume and update-type distribution.
- Summary caching design is deferred until the tracker has real volume data.
