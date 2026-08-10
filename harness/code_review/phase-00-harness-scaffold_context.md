# Phase 00 Code Review

## Review Pass 2026-08-10

### Reviewer Level

Senior software engineer reviewer.

### Scope Reviewed

Initial FastAPI, Postgres, Grafana, Docker Compose, Congress.gov gateway, scheduler state, secret handling, and phase harness scaffold.

### Accepted Findings

- Docker image schema path could fail after packaging because `sql/001_init.sql` was copied to `/app/sql` while `db.py` resolved from package ancestry.
- Gateway instantiated a Congress client but made raw `requests` calls and used an incorrect import path for the selected SDK.
- Text-version collection could count older text versions when a bill had a current-day non-text update.
- Dashboard `next_run_at` would remain empty until the first poll started.
- Compose exposed `CONGRESS_API_KEY` as a plain container environment variable.
- Postgres and FastAPI ports were published on all interfaces despite only Grafana needing LAN access.
- The unpinned GitHub dependency made Pi builds less reproducible.

### Addressed Findings

- Added schema-path discovery that finds `/app/sql/001_init.sql` in containers and the repo-local SQL file in development.
- Switched dependency to `congress-py==0.1.0`, verified the package import surface, and routed API calls through `CongressClient._get`.
- Filtered text-version observations against the active collection window.
- Persisted `next_run_at` during FastAPI startup before the first scheduled poll.
- Moved the Congress API key into a Docker secret sourced from the shell `CONGRESS_API_KEY`.
- Bound Postgres and FastAPI host ports to `127.0.0.1`; Grafana remains LAN-accessible on port `3000`.
- Replaced the GitHub dependency with the pinned published package.

### Deferred Findings

- A live `docker compose up --build` smoke test is deferred until networked dependency installation and live API access are intentionally allowed.
- Dashboard panel behavior should be checked with real accumulated data after the first Pi/laptop run.

### Cancelled Findings

None.

### Verification Notes

- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `python3 -m compileall src tests scripts`
- `python3 scripts/validate_harness.py`
- `env CONGRESS_API_KEY=redacted-for-compose-validation docker compose --env-file .env.example config`
