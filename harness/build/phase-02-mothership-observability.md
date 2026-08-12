# Phase 02: Mothership Observability and Landing

## Objective

Make the tracker operationally visible in Grafana and provide a simple Mothership landing page for the Pi's local tools.

## Context Inputs

- `harness/context/phase-02-mothership-observability_context.md`
- `AGENTS.md`
- `harness/build/phase-01-ntfy-self-hosting.md`

## Build Instructions

1. Add pinned Loki and Grafana Alloy services to Docker Compose.
2. Configure Loki for private local storage and 30-day retention.
3. Configure Alloy to collect Docker and nginx metadata logs without high-cardinality or sensitive labels.
4. Emit safe structured tracker poll lifecycle events.
5. Provision a Loki datasource and Mothership Activity dashboard in Grafana.
6. Serve a static local Pico CSS Mothership landing page at the root nginx route.
7. Extend Ansible health checks and documentation for the new services and routes.

## Acceptance Criteria

- Grafana can query Docker, nginx, and tracker lifecycle logs through Loki.
- Logs persist across Loki and Alloy restarts and expire after 30 days.
- No request bodies, credentials, secrets, or ntfy message content are retained in tracker-generated logs.
- The root page links to the known n8n and Grafana routes without changing existing routes.
- Deployment remains repeatable through Ansible on the Pi.

## Test Plan

- Run Python unit tests and add coverage for structured poll events and secret exclusion.
- Validate Docker Compose, nginx, Ansible syntax, and Grafana dashboard JSON.
- Smoke-test the root page, Loki and Alloy health, datasource/dashboard provisioning, and emitted logs.
- Use an L6 review pass; record findings in `harness/code_review/phase-02-mothership-observability_context.md`, address or explicitly cancel each finding, and obtain reviewer verification.

## GitHub Gate

Commit, push, and PR creation require explicit human approval.
