CREATE TABLE IF NOT EXISTS update_events (
    id BIGSERIAL PRIMARY KEY,
    event_key TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    bill_congress INTEGER,
    bill_type TEXT,
    bill_number TEXT,
    update_date TIMESTAMPTZ NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS update_events_update_date_idx ON update_events (update_date);
CREATE INDEX IF NOT EXISTS update_events_source_type_idx ON update_events (source_type);

CREATE TABLE IF NOT EXISTS daily_update_rollups (
    day DATE NOT NULL,
    source_type TEXT NOT NULL,
    update_count INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (day, source_type)
);

CREATE TABLE IF NOT EXISTS poll_runs (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    inserted_events INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    next_run_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS scheduler_state (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    is_running BOOLEAN NOT NULL DEFAULT false,
    last_started_at TIMESTAMPTZ,
    last_finished_at TIMESTAMPTZ,
    last_status TEXT,
    last_inserted_events INTEGER NOT NULL DEFAULT 0,
    next_run_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO scheduler_state (id)
VALUES (1)
ON CONFLICT (id) DO NOTHING;

CREATE OR REPLACE VIEW dashboard_daily_totals AS
SELECT
    day,
    SUM(update_count) AS total_updates
FROM daily_update_rollups
GROUP BY day;

