# Phase 02 Code Review: Mothership Observability and Landing

## Review Pass 2026-08-10

### Reviewer Level

L6 senior software engineer reviewer.

### Scope Reviewed

The uncommitted `feature/phase-02-mothership-observability` diff against `main`, project guidance in `AGENTS.md`, and the Phase 02 context/build records. The review covered Compose, Loki, Alloy, Grafana provisioning and dashboards, nginx, collector logging, Ansible deployment checks, landing assets, documentation, and tests.

## Findings

- [P0] Raw tracker exception traces can leak `CONGRESS_API_KEY` into Loki -- alloy/config.alloy:31
  Alloy forwards every tracker stdout/stderr line to Loki. The gateway puts the API key in a request query string at `src/bill_update_tracker/congress_gateway.py:112-115`, but redacts only `requests.HTTPError` at lines 117-123. A timeout, connection error, or another `requests.RequestException` is re-raised by `src/bill_update_tracker/collector.py:90`; APScheduler then writes its traceback, including the request URL, to tracker stderr. This violates the project instruction and Phase 02 acceptance criterion that API keys never enter logs.
  Evidence: The Compose service mounts the real key into the tracker, `loki.source.docker` forwards raw container output, and no test covers a non-HTTP request failure.
  Suggested fix: Normalize every `requests.RequestException` in the gateway into a safe, message-free exception before it reaches the scheduler, retaining only a bounded error type/status. Add a fixture-backed timeout/connection-error test that asserts neither the key nor a URL query string is emitted or persisted.

- [P1] The Activity dashboard cannot show the required latest poll result -- grafana/dashboards/mothership-activity.json:6
  The dashboard has only a failure-count stat, a total-log-count stat, activity-by-service, and an unfiltered log stream. It has no query or panel for the latest `poll_succeeded`/`poll_failed` event, its timestamp, or the safe result fields (`inserted_events`, `observed_events`, `error_type`). Operators therefore cannot answer whether the most recent poll succeeded or what it did from the promised Activity view.
  Evidence: `src/bill_update_tracker/collector.py:63-89` emits the safe lifecycle data, but the dashboard only filters for `poll_failed` at line 12 and otherwise uses `{service=~"$service"}`.
  Suggested fix: Add an explicitly titled latest-poll-result panel or table that selects the most recent structured lifecycle event and displays its status, time, and safe result fields. Add a matching dashboard JSON assertion or Grafana smoke check.

- [P2] Alloy adds an unapproved label and reports the wrong host outside the Pi -- alloy/config.alloy:36
  Phase 02 limits labels to `service`, `container`, `stream`, and `host`, but both processing pipelines add `source` at lines 43-47 and 71-75. In addition, all streams hard-code `host = "deathstar"`, so a laptop deployment is mislabeled despite the project requirement to remain deployable on either a laptop or Raspberry Pi.
  Evidence: The Phase 02 context names the allowed label set, while the Alloy configuration adds `source` and fixes the host name in both Docker and nginx targets.
  Suggested fix: Remove the `source` static labels and source the `host` label from a documented deployment setting that defaults appropriately for local runs and is set to the Pi host by Ansible.

## Test Gaps / Residual Risk

- `ansible-playbook --syntax-check`, `docker compose config --quiet`, Python unit tests, compilation, and harness validation pass, but none invokes the Loki or Alloy parsers or provisions the Activity dashboard in a running Grafana instance.
- The current test only proves that a hand-selected safe payload serializes. It does not exercise poll start/success/failure or prove that request failures and raw Docker collection cannot expose sensitive values.
- The Docker socket mount is required for the selected discovery approach, but a read-only socket bind does not limit Docker API calls; treat the Alloy container as privileged operational infrastructure and keep it off the LAN.

## Phase Review Status

- Overall status: **changes requested**; the P0 and P1 findings must be addressed before Phase 02 can be accepted.
- Pending main-thread disposition: P0 raw exception redaction, P1 latest poll result panel, and P2 label/host contract.
- Required reviewer follow-up: after the main thread records each finding as addressed or explicitly cancelled/out of scope, rerun the relevant unit/config/deployment checks and request this reviewer to verify the final dispositions.

## Main-Thread Dispositions 2026-08-10

- [P0] Addressed. `CongressGateway` now normalizes every `requests.RequestException` into `CongressGatewayError` with only a type and optional HTTP status. `run_once`, the scheduler, and the CLI use safe failure boundaries so they do not emit raw exception traces or persist raw exception messages. `tests/test_gateway.py` uses a fixture-free timeout simulation to verify unsafe request text never appears in the raised error.
- [P1] Addressed. `grafana/dashboards/mothership-activity.json` now contains a `Latest Poll Result` log panel filtered to structured `poll_succeeded` and `poll_failed` events. `tests/test_collector.py` asserts the panel and filter exist.
- [P2] Addressed. Removed the unapproved `source` label. Alloy obtains `host` from `ALLOY_HOST_LABEL`, which defaults to `localhost` locally and is set from `app_public_host` by Ansible on the Pi.

## Main-Thread Verification 2026-08-10

- `PYTHONPATH=src python3 -m unittest discover -s tests` (13 tests passed)
- `python3 -m compileall src tests scripts`
- `python3 scripts/validate_harness.py`
- `env CONGRESS_API_KEY=redacted-for-compose-validation docker compose --env-file .env.example config --quiet`
- `ansible-playbook -i ansible/inventory.example.yml ansible/deploy.yml --syntax-check`
- JSON parsing for the Grafana dashboard files
- `git diff --check`

## Reviewer Follow-Up 2026-08-10

### P0 Disposition: Verified Addressed

`CongressGateway._get` now converts both HTTP and non-HTTP `requests.RequestException` failures into `CongressGatewayError` without request URLs or response bodies. `run_once` persists and logs only an exception type, then raises `PollRunFailed` without a chained traceback; the scheduler and CLI contain that safe boundary. The timeout test uses an API-key-bearing URL as adversarial input and verifies that the resulting error contains neither the key nor a URL.

### P1 Disposition: Verified Addressed

The `Latest Poll Result` logs panel targets only tracker `poll_succeeded` and `poll_failed` JSON events, renders JSON fields, and sorts newest first. It therefore shows the most recent outcome, timestamp, and the safe success/failure metadata emitted by the collector. The dashboard JSON test asserts the panel and lifecycle filter exist.

### P2 Disposition: Verified Addressed

The unapproved `source` labels have been removed. All Docker and nginx streams source their `host` label from `ALLOY_HOST_LABEL`; Compose defaults it to `localhost` for laptop use, and Ansible writes `app_public_host` for the Pi deployment. The remaining configured labels are limited to the Phase 02 set: `service`, `container`, `stream`, and `host`.

No remaining blocking review findings.

### Residual Runtime Verification

- Static validation passed again: 13 Python tests, compilation, harness validation, Compose rendering, Ansible syntax validation, dashboard JSON parsing, and `git diff --check`.
- The local Docker daemon is unavailable to this reviewer, so Alloy and Loki could not be started to parse their configuration or prove live ingestion. The Phase 02 deployment smoke checks must still verify Alloy/Loki readiness, Grafana provisioning, tracker lifecycle logs, nginx logs, and ntfy metadata-only logging before final deployment acceptance.

### Final Review Status

- P0: verified addressed.
- P1: verified addressed.
- P2: verified addressed.
- Reviewer status: approved for the planned deployment verification; no cancelled findings.

### Follow-Up Addendum

- `tests/test_mothership_assets.py` was added during reviewer follow-up. It verifies the landing links and Pico asset and guards the configurable Alloy host label plus removal of the prior `source` labels. The complete current suite passes with 15 tests.

## Verification Performed

- `git diff --check main`
- `ansible-playbook --syntax-check -i ansible/inventory.example.yml ansible/deploy.yml`
- `docker compose config --quiet`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=src python3 -m compileall -q src tests`
- `python3 scripts/validate_harness.py`
- JSON parsing for the Grafana dashboard files
