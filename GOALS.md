# Goals

## Product Goal

Track how many Congress.gov bill-related updates occur per day and expose the data in Grafana so downstream projects can estimate the volume and type of LLM summarization work they might need.

## MVP

- Run locally on a laptop with Docker Compose.
- Deploy unchanged to a Raspberry Pi.
- Poll Congress.gov hourly.
- Store raw update events and daily rollups in Postgres.
- Show total update counts and update-type breakdowns in Grafana.
- Show last poll time, next scheduled poll time, and running status.

## Non-Goals For Initial Scaffold

- No LLM summarization implementation.
- No user authentication.
- No public internet exposure guidance beyond LAN dashboard access.

