# Phase 01: LAN-Only ntfy Self-Hosting

## Goal

Host a private ntfy server on the Raspberry Pi so local services can publish operational notifications without exposing a new service to the public internet.

## Desired Outcome

- ntfy runs on the Pi through Docker Compose.
- ntfy is reachable on the LAN through nginx at `http://deathstar.local/ntfy/`.
- ntfy is not directly exposed on a public interface; the container port binds to `127.0.0.1`.
- ntfy data persists across container restarts and deploys.
- publishing requires authentication by default.
- deployment remains repeatable through Ansible.
- no ntfy passwords, tokens, or generated credentials are committed.

## Assumptions

- This is LAN-only or VPN-only. No router port forwarding, public DNS, or public TLS is part of this phase.
- The Pi already has Docker, Docker Compose, nginx, and UFW handling from the existing deployment path.
- The default install path remains `/opt/bill-update-tracker`.
- ntfy state can live under `/opt/bill-update-tracker/runtime/ntfy` unless a later storage review picks a thumb-drive path.
- ntfy credentials are supplied from `NTFY_AUTH_USERS` in the controller environment during deploy, similar to `CONGRESS_API_KEY`.

## Non-Goals

- Internet-accessible mobile push.
- TLS certificate automation.
- SMTP/email integration.
- UnifiedPush setup.
- Alerting rules that depend on ntfy.
- Migrating this project to multiple Compose projects.

## Implementation Plan

1. Add ntfy configuration to Docker Compose.
   - Add a `ntfy` service using `binwiederhier/ntfy`.
   - Run `ntfy serve`.
   - Bind `127.0.0.1:8093:80`.
   - Mount persistent data at `/var/lib/ntfy`.
   - Set `NTFY_BASE_URL=http://deathstar.local:8093`; ntfy does not accept a path in its canonical base URL, while nginx still exposes `/ntfy/` as the LAN convenience route.
   - Set `NTFY_BEHIND_PROXY=true`.
   - Set `NTFY_CACHE_FILE=/var/lib/ntfy/cache.db`.
   - Set `NTFY_AUTH_FILE=/var/lib/ntfy/auth.db`.
   - Set `NTFY_AUTH_DEFAULT_ACCESS=deny-all`.
   - Set `NTFY_ENABLE_LOGIN=true`.
   - Add a healthcheck against `/v1/health`.

2. Add Ansible variables for ntfy.
   - `ntfy_enabled: true`
   - `ntfy_host_bind: 127.0.0.1`
   - `ntfy_host_port: 8093`
   - `ntfy_public_path: /ntfy/`
   - `ntfy_base_url: http://deathstar.local:8093`
   - `ntfy_data_dir: "{{ app_install_dir }}/runtime/ntfy"`

3. Add secret handling for ntfy auth.
   - Require local deploy environment variables for the initial ntfy admin user and password hash or password.
   - Pass bcrypt hashes to Compose as `NTFY_AUTH_USERS` so plaintext ntfy passwords are not written to disk.
   - Document how to generate the bcrypt hash locally.
   - Do not read or print secret files during normal work.

4. Add persistent directory creation.
   - Create `{{ ntfy_data_dir }}` on the Pi.
   - Restrict permissions enough for the container to use it while avoiding world-writable state.
   - Keep generated ntfy databases out of Git.

5. Add nginx routing.
   - Add a second nginx location for `{{ ntfy_public_path }}` in the existing server block.
   - Proxy to `http://127.0.0.1:{{ ntfy_host_port }}`.
   - Include standard forwarded headers.
   - Preserve WebSocket/long-polling behavior if ntfy needs upgraded connections.

6. Add Prometheus integration if ntfy metrics are enabled.
   - Enable ntfy metrics only if the server supports a no-secret `/metrics` endpoint for this deployment mode.
   - Add a Prometheus scrape target for `ntfy:80`.
   - Defer Grafana ntfy panels unless the metrics surface proves useful.

7. Update documentation.
   - Add a short ntfy section to `README.md`.
   - Add deploy instructions to `ansible/README.md`.
   - Include local publish and subscribe smoke-test commands.
   - State explicitly that the service is LAN-only by default.

8. Verify locally without secrets.
   - `docker compose --env-file .env.example config --quiet`
   - `ansible-playbook -i ansible/inventory.example.yml ansible/deploy.yml --syntax-check`
   - `python3 scripts/validate_harness.py`
   - Secret scan for committed ntfy credentials.

9. Deploy and smoke test on the Pi.
   - Deploy with Ansible.
   - Check `docker compose ps ntfy`.
   - Check `http://127.0.0.1:8093/v1/health` on the Pi.
   - Check `http://deathstar.local/ntfy/` from the laptop.
   - Publish a test notification to an authenticated topic.
   - Subscribe from browser or CLI and verify delivery.

## Open Questions Before Implementation

- ntfy uses `/opt/bill-update-tracker/runtime/ntfy` for this phase; the attached thumb drive can be selected later by changing `ntfy_data_dir`.
- The LAN route is `http://deathstar.local/ntfy/` for this phase.
- The first account is provisioned through `NTFY_AUTH_USERS`; the username is intentionally not committed.
- Authenticated users can publish to topics according to their ntfy role for this phase.

## Acceptance Criteria

- A repeatable Ansible deploy creates or updates ntfy without manual container commands.
- ntfy survives container restart with its auth database and cache intact.
- unauthenticated publishing is denied.
- authenticated publishing succeeds.
- LAN access through nginx works.
- no ntfy credentials or Congress.gov credentials appear in tracked files, untracked project files, command output, or screenshots.
