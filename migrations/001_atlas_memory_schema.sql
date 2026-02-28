-- Atlas stateful agent memory schema for Postgres (Railway).
-- Run once to create tables (e.g. via scripts/init_db.py or psql).

-- Short-term: recent conversation + current cache (command stack, data collection, etc.)
CREATE TABLE IF NOT EXISTS short_term_memory (
    user_id TEXT PRIMARY KEY,
    recent_messages JSONB NOT NULL DEFAULT '[]',
    current_cache JSONB NOT NULL DEFAULT '{}',
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    expires_at DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Long-term: user facts and recent command results
CREATE TABLE IF NOT EXISTS long_term_memory (
    user_id TEXT PRIMARY KEY,
    facts TEXT NOT NULL DEFAULT '',
    recent_results JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Optional: index for expiry cleanup
CREATE INDEX IF NOT EXISTS idx_short_term_expires_at ON short_term_memory (expires_at);
