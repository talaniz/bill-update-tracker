# Ansible Deployment

This deploys Bill Update Tracker to `palpatine@deathstar.local`.

## One-Time Setup

Install Ansible on the laptop if `ansible-playbook` is not already available:

```bash
brew install ansible
```

Create a local inventory from the example:

```bash
cp ansible/inventory.example.yml ansible/inventory.yml
```

`ansible/inventory.yml` is ignored by Git.

## Read-Only Target Check

```bash
ansible-playbook -i ansible/inventory.yml ansible/check.yml
```

## Deploy

Source the local secrets file on the laptop before deploying. The playbook reads
`CONGRESS_API_KEY` from the controller environment and passes it to Docker Compose
as a Docker secret. The key is not written to the repo.

The playbook also requires `NTFY_AUTH_USERS` so ntfy starts with at least one
authenticated user. The value must use ntfy's declarative user format:

```text
username:bcrypt-hash:role
```

Generate the bcrypt hash locally with the ntfy image:

```bash
docker run --rm -it binwiederhier/ntfy:v2.26.3 user hash
```

If you store `NTFY_AUTH_USERS` in `~/.zshrc.secrets`, quote the value so the
shell preserves the bcrypt `$` characters. The deploy template escapes the hash
when writing the Pi's Docker Compose `.env` file.

```bash
source ~/.zshrc.secrets
ansible-playbook -i ansible/inventory.yml ansible/deploy.yml --ask-become-pass
```

Expected route after deploy:

```text
http://deathstar.local/bill-update-tracker/
```

Expected ntfy route after deploy:

```text
http://deathstar.local/ntfy/
```

## Notes

- Docker and Docker Compose must already be installed on the Pi.
- The app is deployed to `/opt/bill-update-tracker`.
- Grafana binds to `127.0.0.1:3000`; Nginx is the public entrypoint.
- FastAPI binds to `127.0.0.1:8000`.
- ntfy binds to `127.0.0.1:8093` and is served by Nginx at `/ntfy/`.
- Postgres remains private to the Docker network.
- If UFW is active, the deploy playbook allows `80/tcp` so the Nginx route is reachable from the LAN.
