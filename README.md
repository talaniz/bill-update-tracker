# Mothership

Track Congress.gov bill update volume over time so downstream projects can estimate how often bill changes might need LLM summarization.

## What It Tracks

- Total bill-related updates per day.
- Bill latest-action updates.
- Bill text-version updates.
- Official Congress.gov summary updates.
- Poll health: last query time, next scheduled query time, and whether a poll is currently running.
- Pi compute health: CPU, load, memory, filesystems, network traffic, file descriptors, and per-container resource usage.
- LAN-only ntfy notifications for operational alerts.
- Mothership operational activity logs in Grafana.

Initial tracking starts from the current day. The default scheduler polls hourly and stores both raw events and daily rollups in Postgres.

By default, the tracker follows the current Congress reported by Congress.gov. This avoids unstable deep pagination across all historical bills while still answering the operational question for active legislative tracking.

## Secret Handling

Do not commit real secrets. Compose reads `CONGRESS_API_KEY` from your shell and mounts it into the tracker container as a Docker secret file. On this machine, the intended local source is `~/.zshrc.secrets`; source it before running commands that need live Congress.gov access.

```bash
source ~/.zshrc.secrets
```

## Run Locally

```bash
cp .env.example .env
source ~/.zshrc.secrets
docker compose up --build
```

Grafana: `http://localhost:3000`

Mothership Activity: `http://localhost:3000/d/mothership-activity/mothership-activity`

ntfy: `http://localhost:8093`

FastAPI health: `http://localhost:8000/health`

FastAPI status: `http://localhost:8000/status`

The dashboard is provisioned at `http://localhost:3000/d/bill-update-tracker/bill-update-tracker`.

The Pi compute dashboard is provisioned at `http://localhost:3000/d/pi-compute-metrics/pi-compute-metrics`.

Loki and Alloy collect container and nginx operational metadata for 30 days. Tracker logs include poll lifecycle metadata only; request bodies, ntfy message content, credentials, and API keys are not logged.

Set `NTFY_AUTH_USERS` before using ntfy locally. The value is a comma-separated list of `username:bcrypt-hash:role` entries. Generate a hash with the ntfy container rather than an online password generator:

```bash
docker run --rm -it binwiederhier/ntfy:v2.26.3 user hash
```

If you put the value in `.env`, escape bcrypt `$` characters as `$$` so Docker Compose preserves the hash.

## Raspberry Pi Deployment

Ansible deployment files live in `ansible/`. The default target is:

```text
palpatine@deathstar.local
```

The default deployment path is `/opt/bill-update-tracker`, and Grafana is served through Nginx at:

```text
http://deathstar.local/bill-update-tracker/
```

Mothership's local landing page is served at `http://deathstar.local/`. It links to Grafana and n8n at `http://deathstar.local:5678/`.

ntfy is served through the same Nginx host at:

```text
http://deathstar.local/ntfy/
```

See `ansible/README.md` for the checked deployment workflow.

For a manual Pi deployment, install Docker and Docker Compose on the Pi, clone this repo, create `.env`, and run:

```bash
docker compose up -d --build
```

From your laptop on the same network, open:

```text
http://<pi-hostname-or-ip>:3000
```

Use a non-default `GRAFANA_ADMIN_PASSWORD` in `.env` before exposing the dashboard on your LAN. Postgres is private to the Docker network and FastAPI is bound to localhost by default; Grafana is the only service published for LAN access.

## Manual Poll

With dependencies installed:

```bash
source ~/.zshrc.secrets
docker compose exec tracker python -m bill_update_tracker.collector run-once
```

## ntfy Smoke Test

After setting `NTFY_AUTH_USERS` and starting the stack, publish a local test notification:

```bash
curl -u '<username>:<password>' \
  -d 'bill-update-tracker ntfy smoke test' \
  http://localhost:8093/bill-update-tracker-test
```

From the deployed Pi route, use:

```bash
curl -u '<username>:<password>' \
  -d 'bill-update-tracker ntfy smoke test' \
  http://deathstar.local/ntfy/bill-update-tracker-test
```

## Verification

Default verification does not call Congress.gov:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall src tests
python3 scripts/validate_harness.py
```

## Notes

The Congress.gov API reports bill, text, and summary updates with different date fields. This tracker stores each observed update with an idempotent event key and uses daily rollups for Grafana.

Host and container metrics are collected by Prometheus from `node-exporter` and cAdvisor. Loki stores container and nginx metadata logs for 30 days, and Alloy ships those logs to Loki. Prometheus, Loki, node_exporter, cAdvisor, and Alloy are private to the Docker network or localhost; Grafana is the UI entrypoint.

ntfy is configured as an authenticated LAN service. Its canonical, pathless endpoint is `http://deathstar.local:8093/`, which ntfy uses for generated links; Nginx also preserves the convenience route at `/ntfy/`. No router port forwarding or public internet exposure is required.
