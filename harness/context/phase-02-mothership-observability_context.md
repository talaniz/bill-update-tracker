# Phase 02 Context: Mothership Observability and Landing

## Requirements Captured

- Use Mothership as the display identity for the landing page, Grafana folder and dashboards, documentation, and Phase 02 records.
- Keep existing repository, Python package, Compose service names, URLs, and `/opt/bill-update-tracker` deployment path stable.
- Add Grafana-native logging with Loki and Alloy, retaining 30 days of metadata-only operational logs on the Pi.
- Add a root landing page at `http://deathstar.local/` that links to n8n and Grafana.
- Use locally vendored Pico CSS rather than a CDN or a JavaScript build pipeline.
- Preserve `/bill-update-tracker/`, `/ntfy/`, and the separate n8n virtual host.

## Decisions

- Run Loki as a private, single-node Docker service with local persistent storage and 30-day retention.
- Use Grafana Alloy to discover Docker logs and read nginx access/error logs. Retain only the labels `service`, `container`, `stream`, and `host`.
- Tracker poll logs are structured JSON events: `poll_started`, `poll_succeeded`, and `poll_failed`.
- Do not log request bodies, ntfy message contents, authentication material, API keys, raw upstream responses, or exception messages.
- The root page uses a local copy of Pico CSS 2.1.1 and links to `http://deathstar.local:5678/` and `http://deathstar.local/bill-update-tracker/`.

## Deferred

- Elastic/Kibana, distributed tracing, alert rules, public internet exposure, and mobile-connectivity changes.
- Moving observability data to the attached thumb drive; the Pi currently has sufficient local capacity.
