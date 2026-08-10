# Bill Update Tracker

## Project Instructions

- Keep `CONGRESS_API_KEY` out of source control, logs, fixtures, screenshots, and examples.
- The local secret source of truth is `~/.zshrc.secrets`; do not read or print it during normal project work.
- Prefer fixture-backed tests for Congress.gov behavior. Use live API calls only for explicit manual smoke checks.
- Keep the tracker deployable with Docker Compose on a laptop or Raspberry Pi.
- Preserve the phase harness files under `harness/` and update them when phase-level decisions change.

