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

```bash
source ~/.zshrc.secrets
ansible-playbook -i ansible/inventory.yml ansible/deploy.yml --ask-become-pass
```

Expected route after deploy:

```text
http://deathstar.local/bill-update-tracker/
```

## Notes

- Docker and Docker Compose must already be installed on the Pi.
- The app is deployed to `/opt/bill-update-tracker`.
- Grafana binds to `127.0.0.1:3000`; Nginx is the public entrypoint.
- FastAPI binds to `127.0.0.1:8000`.
- Postgres remains private to the Docker network.
