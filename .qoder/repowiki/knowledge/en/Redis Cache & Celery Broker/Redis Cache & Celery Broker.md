---
kind: external_dependency
name: Redis Cache & Celery Broker
slug: redis
category: external_dependency
category_hints:
    - client_constraint
scope:
    - '**'
---

### Redis 7 (in-memory cache + message broker)
- Role: Dual-purpose: SHA256 image hash cache (`IMAGE_CACHE_TTL=604800`) and Celery broker/result backend (`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`).
- Client constraint: Docker Compose exposes port 6379; development `.env` defaults to `redis://localhost:6379/{0,1}`.
- Not a code-invisible dependency beyond what manifests declare — included only because conversation confirms it is wired for both caching and task queue.