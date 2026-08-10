# Phase 00 - Harness Scaffold

## Objective

Create the initial repository scaffold, phase harness, and runnable project skeleton for the bill update tracker.

## Design Source

User-provided requirements in the Codex thread on 2026-08-10.

## Context Inputs

- `harness/context/phase-00-harness-scaffold_context.md`
- `AGENTS.md`
- `GOALS.md`

## Build Instructions

- Initialize the repository.
- Add harness files.
- Add a minimal FastAPI, Postgres, and Grafana Docker Compose scaffold.
- Keep all secrets out of committed files.

## Acceptance Criteria

- Project files exist and are version-control ready.
- `CONGRESS_API_KEY` is documented as an environment variable only.
- Tests and syntax checks can run without live API access.
- Grafana provisioning points at Postgres.

## Test Plan

- Run Python compile checks.
- Run fixture-backed unit tests.
- Validate that required harness files exist.

## Verification Commands

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall src tests
python3 scripts/validate_harness.py
```

## Risks And Deferrals

- Live Congress.gov client behavior requires a later smoke test with a real API key.
- Dashboard panel tuning should be revisited after real data accumulates.

## Red Green Refactor Review

Use fixture-backed red/green checks for event normalization and rollup behavior.

## GitHub Gate

Commit, push, and PR creation require explicit human approval.

## Phase Completion Notes

Pending.
