# Bill Update Tracker

Track Congress.gov bill update volume over time so downstream projects can estimate how often bill changes might need LLM summarization.

## What It Tracks

- Total bill-related updates per day.
- Bill latest-action updates.
- Bill text-version updates.
- Official Congress.gov summary updates.
- Poll health: last query time, next scheduled query time, and whether a poll is currently running.

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

FastAPI health: `http://localhost:8000/health`

FastAPI status: `http://localhost:8000/status`

The dashboard is provisioned at `http://localhost:3000/d/bill-update-tracker/bill-update-tracker`.

## Raspberry Pi Deployment

Ansible deployment files live in `ansible/`. The default target is:

```text
palpatine@deathstar.local
```

The default deployment path is `/opt/bill-update-tracker`, and Grafana is served through Nginx at:

```text
http://deathstar.local/bill-update-tracker/
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

## Verification

Default verification does not call Congress.gov:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall src tests
python3 scripts/validate_harness.py
```

## Notes

The Congress.gov API reports bill, text, and summary updates with different date fields. This tracker stores each observed update with an idempotent event key and uses daily rollups for Grafana.
