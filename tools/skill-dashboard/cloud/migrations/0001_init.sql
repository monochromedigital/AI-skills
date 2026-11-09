-- Monochrome console: what each Mac sends up from its local ledger.
-- Ids come from the transcripts themselves (tool_use ids, message ids), so
-- re-sending a row is harmless: inserts ignore ids already stored.
-- Times are ISO-8601 UTC text, which SQLite sorts and compares correctly.

CREATE TABLE machines (
  id          TEXT PRIMARY KEY,                 -- random id made once per Mac (machine.json)
  name        TEXT NOT NULL,
  first_seen  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  last_sync   TEXT
);

-- One row per skill use (the model calling a skill, or you typing /skill).
CREATE TABLE skill_events (
  id          TEXT PRIMARY KEY,
  machine_id  TEXT NOT NULL REFERENCES machines(id),
  ts          TEXT NOT NULL,
  skill       TEXT NOT NULL,
  via         TEXT NOT NULL,                    -- 'model' | 'slash'
  session_id  TEXT,
  project     TEXT,                             -- the session's folder, home shortened to ~
  subagent    INTEGER NOT NULL DEFAULT 0,
  entrypoint  TEXT,
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX skill_events_ts      ON skill_events (ts);
CREATE INDEX skill_events_skill   ON skill_events (skill, ts);
CREATE INDEX skill_events_project ON skill_events (project, ts);
CREATE INDEX skill_events_machine ON skill_events (machine_id, ts);

-- One row per Claude reply: the raw material for cost per project and session.
CREATE TABLE token_usage (
  id              TEXT PRIMARY KEY,             -- Claude message id
  machine_id      TEXT NOT NULL REFERENCES machines(id),
  ts              TEXT NOT NULL,
  model           TEXT,
  session_id      TEXT,
  project         TEXT,
  subagent        INTEGER NOT NULL DEFAULT 0,
  input_tokens    INTEGER NOT NULL DEFAULT 0,
  output_tokens   INTEGER NOT NULL DEFAULT 0,
  cache_write_5m  INTEGER NOT NULL DEFAULT 0,
  cache_write_1h  INTEGER NOT NULL DEFAULT 0,
  cache_read      INTEGER NOT NULL DEFAULT 0,
  web_searches    INTEGER NOT NULL DEFAULT 0,
  created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX token_usage_ts      ON token_usage (ts);
CREATE INDEX token_usage_project ON token_usage (project, ts);
CREATE INDEX token_usage_session ON token_usage (session_id);
CREATE INDEX token_usage_model   ON token_usage (model, ts);
CREATE INDEX token_usage_machine ON token_usage (machine_id, ts);

-- Session titles: yours if you named the session, else the generated one.
CREATE TABLE sessions (
  id          TEXT PRIMARY KEY,
  machine_id  TEXT NOT NULL REFERENCES machines(id),
  title       TEXT,
  custom      INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX sessions_machine ON sessions (machine_id);

-- The latest full dashboard per Mac (skills, updates, MCP status, groups, ...),
-- exactly what the local page renders, in read-only form.
CREATE TABLE snapshots (
  machine_id    TEXT PRIMARY KEY REFERENCES machines(id),
  generated_at  TEXT NOT NULL,
  report        TEXT NOT NULL CHECK (json_valid(report))
);

-- Prices per million tokens, per model, for the cost view (filled later).
CREATE TABLE model_prices (
  model                    TEXT PRIMARY KEY,
  input_per_mtok           REAL NOT NULL,
  output_per_mtok          REAL NOT NULL,
  cache_write_5m_per_mtok  REAL NOT NULL,
  cache_write_1h_per_mtok  REAL NOT NULL,
  cache_read_per_mtok      REAL NOT NULL,
  updated_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
