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

## Final Commit Review 2026-08-10

### Scope

Review of `b0d9c05` (`Fix ntfy canonical base URL`) and `4f058ac` (`Handle existing Grafana admin credentials`) against their runtime deployment contracts.

### Findings

- [P1] The advertised ntfy base URL is unreachable from LAN clients -- ansible/group_vars/all.yml:34
  `NTFY_BASE_URL` now advertises `http://deathstar.local:8093`, but the same Ansible template sets `NTFY_HOST_BIND=127.0.0.1` and Compose publishes port 8093 only on that loopback interface. The only LAN-reachable route is nginx on port 80 at `/ntfy/`, which cannot serve as ntfy's pathless canonical root. Generated ntfy links, including attachment URLs, will therefore point clients at an unreachable endpoint.
  Evidence: `ansible/templates/tracker.env.j2:14-16`, `docker-compose.yml:149,159`, and `ansible/templates/nginx-bill-update-tracker.conf.j2:32-33` show the conflicting external URL, loopback bind, and proxy route. ntfy documents `base-url` as the external/root URL used for generated attachment links.
  Suggested fix: Make one pathless canonical URL externally reachable: either deliberately publish port 8093 to the LAN with the existing authentication controls, or give ntfy its own nginx host/port that proxies to loopback. Set `NTFY_BASE_URL` to that reachable root URL and add a separate-LAN-client smoke test for it.

- [P1] The Grafana existing-admin fallback checks a path that is not mounted -- ansible/deploy.yml:199
  The new fallback is meant to let an existing Grafana database with a different admin password deploy successfully, but it tests `/etc/grafana/dashboards/mothership-activity.json`. Compose mounts dashboards at `/var/lib/grafana/dashboards`, not `/etc/grafana/dashboards`, so the command exits nonzero and aborts every deploy that reaches it.
  Evidence: `docker-compose.yml:57-58` mounts the provisioning directory and dashboard directory at distinct locations; the deploy command checks the datasource mount correctly at line 198 and the dashboard mount incorrectly at line 199. The added test asserts only that the task exists, not its container path.
  Suggested fix: Check `/var/lib/grafana/dashboards/mothership-activity.json`, and strengthen the test to assert that exact mounted path. Retain the `200`/`401` API handling once this fallback can execute.

### Dispositions

- `b0d9c05`: rejected pending the reachable canonical ntfy root URL correction.
- `4f058ac`: partially accepted for tolerating an existing Grafana admin password, but rejected pending the mounted-dashboard-path correction.
- Final status: changes requested; do not treat Phase 02 as deployment-ready until both P1 findings are addressed and re-reviewed.

### Verification

- 17 Python tests, compilation, harness validation, Compose rendering, Ansible syntax validation, dashboard JSON parsing, and diff checks pass.
- Those static checks do not exercise a LAN client following the ntfy base URL or `docker compose exec` inside Grafana, which is why both deployment errors escaped the added tests.

## P1 Remediation Verification 2026-08-10

### ntfy Canonical URL: Verified Addressed

The Pi inventory now renders `NTFY_HOST_BIND=0.0.0.0`, `NTFY_HOST_PORT=8093`, and `NTFY_BASE_URL=http://deathstar.local:8093`. A simulated Pi Compose render publishes `0.0.0.0:8093:80`, while the existing nginx `/ntfy/` proxy remains unchanged. The deploy playbook adds the matching `ufw allow {{ ntfy_host_port }}/tcp` rule when UFW is active, and the README, Ansible documentation, phase context, and static test cover the canonical endpoint and LAN bind.

### Grafana Existing-Admin Fallback: Verified Addressed

The fallback now checks `/var/lib/grafana/dashboards/mothership-activity.json`, matching the Compose dashboard mount. The corresponding test asserts the corrected path, while the authenticated `200`/`401` probes continue to accommodate an existing Grafana data volume with a different administrator password.

### Final Dispositions

- P1 ntfy canonical URL: verified addressed; no longer remains.
- P1 Grafana existing-admin fallback: verified addressed; no longer remains.
- No P1 findings remain from the Final Commit Review.

### Remaining Actionable Finding

- [P2] Phase 01 desired outcome still describes the superseded loopback-only ntfy deployment -- harness/build/phase-01-ntfy-self-hosting.md:11
  The Phase 01 build record now implements and documents authenticated LAN access at `0.0.0.0:8093`, but its Desired Outcome still says the container binds to `127.0.0.1`. This leaves the durable harness contradictory for later deployment or security work.
  Evidence: Lines 39-54 in the same file specify the LAN bind and canonical URL.
  Suggested fix: Replace the loopback-only Desired Outcome bullet with the approved authenticated, UFW-controlled LAN endpoint while retaining the no-public-internet constraint.

### Residual Runtime Verification

- Static checks pass: 17 Python tests, compilation, harness validation, Compose rendering, Ansible syntax validation, dashboard JSON parsing, and diff checks.
- A real Pi deployment is still required to confirm the UFW rule is applied and a separate LAN client can reach the canonical ntfy URL.

## P2 Final Verification 2026-08-10

### Disposition: Not Addressed

The Phase 01 Goal now correctly says authenticated LAN-only, but its Desired Outcome still states that the container port binds to `127.0.0.1` at `harness/build/phase-01-ntfy-self-hosting.md:11`. This directly conflicts with the same file's approved `0.0.0.0:8093` implementation at lines 39 and 51 and with the current Ansible deployment variables.

### Current Review State

- P0 tracker logging boundary: verified addressed.
- P1 Activity dashboard latest result: verified addressed.
- P2 Alloy label/host contract: verified addressed.
- P1 ntfy canonical URL: verified addressed.
- P1 Grafana existing-admin fallback: verified addressed.
- P2 Phase 01 Desired Outcome: remains open pending removal of the loopback-only statement.

Final disposition: Phase 02's implementation findings are addressed, but the review record cannot mark all current P1/P2 findings addressed until the stale Desired Outcome bullet is corrected and re-reviewed.

## P2 Closure Verification 2026-08-10

### Disposition: Verified Addressed

The Phase 01 Desired Outcome now states that ntfy is exposed only to the LAN on port `8093` for its pathless canonical URL and that no public internet exposure is configured. This matches the authenticated `0.0.0.0:8093` deployment contract, UFW rule, canonical base URL, and retained nginx `/ntfy/` route.

### Final Finding Status

- P0 tracker logging boundary: verified addressed.
- P1 Activity dashboard latest result: verified addressed.
- P2 Alloy label/host contract: verified addressed.
- P1 ntfy canonical URL: verified addressed.
- P1 Grafana existing-admin fallback: verified addressed.
- P2 Phase 01 Desired Outcome: verified addressed.

No current P1 or P2 findings remain. The remaining Pi deployment checks are runtime acceptance verification, not unresolved review findings.

## Verification Performed

- `git diff --check main`
- `ansible-playbook --syntax-check -i ansible/inventory.example.yml ansible/deploy.yml`
- `docker compose config --quiet`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=src python3 -m compileall -q src tests`
- `python3 scripts/validate_harness.py`
- JSON parsing for the Grafana dashboard files
