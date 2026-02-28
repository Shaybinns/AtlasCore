# Railway deployment (Atlas stateful agent)

## Postgres and DB setup

1. **Add Postgres** in the Railway project (Dashboard → your service → Variables → Add PostgreSQL plugin, or New → Database → PostgreSQL). Railway will set `DATABASE_URL` automatically.

2. **Create tables once** after the first deploy (or before first use):
   - In Railway: open your service → **Settings** → run a one-off command, or use the shell:
   ```bash
   python scripts/init_db.py
   ```
   - Or locally with the same `DATABASE_URL`:
   ```bash
   set DATABASE_URL=postgresql://...
   python scripts/init_db.py
   ```

3. **Schema** is in `migrations/001_atlas_memory_schema.sql`:
   - `short_term_memory`: `user_id`, `recent_messages` (JSONB), `current_cache` (JSONB), `created_at`, `expires_at`
   - `long_term_memory`: `user_id`, `facts` (text), `recent_results` (JSONB), `created_at`, `updated_at`

## Required env vars

- `DATABASE_URL` – set by Railway when Postgres is added.
- `OPENAI_API_KEY` – for LLM fallback.
- `OPENROUTER_API_KEY` – optional; for Atlas intent-based model routing.

## Cron

The existing `railway.json` cron runs daily cleanup of expired short-term entries. Ensure the app has a cron runner or run `python -c "from memory.short_term_cache import cleanup_expired_entries; cleanup_expired_entries()"` periodically.

## Start command

Default start is `python api_server.py`. For production, Railway/Nixpacks may use `gunicorn` if present (see `requirements.txt`).
