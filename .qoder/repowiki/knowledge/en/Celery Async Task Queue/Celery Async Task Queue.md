---
kind: external_dependency
name: Celery Async Task Queue
slug: celery
category: external_dependency
category_hints:
    - framework_behavior
scope:
    - '**'
---

### Celery 5.4 with Redis broker
- Role: Background worker process (`omnishield-celery`) consuming tasks from the Redis broker; currently initialized but video moderation uses FastAPI `BackgroundTasks` instead of Celery tasks.
- Framework behavior: Celery app is configured with JSON serializers and imports `app.tasks`; workers are started via `celery -A app.core.celery_app worker --loglevel=info` in compose.