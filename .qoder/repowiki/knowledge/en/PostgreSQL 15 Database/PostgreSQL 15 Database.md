---
kind: external_dependency
name: PostgreSQL 15 Database
slug: postgresql
category: external_dependency
category_hints:
    - client_constraint
scope:
    - '**'
---

### PostgreSQL 15 (production) / SQLite (development)
- Role: Persistent store for users, API keys, moderation logs, and video moderation records.
- Client constraint: `DATABASE_URL` auto-converted to `postgresql+asyncpg://` when not sqlite; default dev URL points at `./moderation.db` via `aiosqlite`.
- Docker Compose provisions `omnishield-postgres` on port 5432 with DB `moderation_db`.