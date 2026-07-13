---
kind: logging_system
name: Loguru-Based Application Logging
category: logging_system
scope:
    - '**'
source_files:
    - backend/app/main.py
    - backend/app/core/config.py
    - backend/app/api/moderate.py
    - backend/app/tasks.py
    - backend/app/repositories/log_repo.py
    - backend/app/models/log.py
    - backend/app/models/video_log.py
    - backend/app/repositories/video_log_repo.py
    - backend/docker-compose.yml
---

The backend uses the third-party **loguru** library (v0.7.2) as its sole logging framework. There is no centralized logger configuration file — loguru is imported directly in each module that needs it and used with default sinks (stdout/stderr). The `logger` singleton from `loguru` is imported at the top of every component: API routers (`api/auth.py`, `api/keys.py`, `api/moderate.py`, `api/analytics.py`), core modules (`core/oauth.py`, `core/rate_limit.py`, `core/redis.py`, `core/security.py`, `core/advanced_rate_limit.py`), services (`services/ai_moderation.py`, `services/hash_cache.py`, `services/multi_model_moderation.py`, `services/video_moderation.py`), background tasks (`tasks.py`), and repositories (`repositories/user_repo.py`).

**Log levels used**: `logger.info`, `logger.warning`, `logger.error`, and `logger.exception` are all present. No custom level strategy or environment-driven level switching exists; the default loguru level applies everywhere.

**Structured fields**: Log messages are plain strings with f-strings, not structured dicts. Examples include `logger.exception(f"Failed to queue video moderation job: {e}")` and `logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} starting up...")`. There is no correlation-id injection, request-context enrichment, or JSON formatter configured.

**Sinks and rotation**: No `logger.add(...)` calls were found anywhere in the codebase, so loguru's defaults are used (console output only). There is no file sink, no rotation, no size limits, and no external sink (no Sentry, Datadog, etc.). Celery workers are started with `--loglevel=info` via CLI flags in `docker-compose.yml` and deployment docs, which controls Celery's own internal logging separately from loguru.

**Application audit logs vs. operational logs**: The project distinguishes between two concepts:
- Operational/debug logs written through loguru (the topic of this card).
- Persistent moderation audit records stored in PostgreSQL via `app/models/log.py` / `app/repositories/log_repo.py` and `app/models/video_log.py` / `app/repositories/video_log_repo.py`. These are database rows (not console logs) capturing user_id, image_hash, decision, risk_level, confidence, detected_labels, bounding_boxes, processing_time, recommended_action, reason, plus extended fields like model_results, model_versions, face_count, detected_text, contains_profanity for comprehensive moderation.

**Frontend**: The Next.js frontend has no logging system of its own; it relies on the browser console and does not ship a client-side logger.

**Rules developers should follow**:
- Import `from loguru import logger` at the top of any module that needs to emit logs.
- Use `logger.info` for normal operational events, `logger.warning` for recoverable issues, `logger.error` for failures, and `logger.exception` when you want the full traceback attached.
- Do not configure loguru yourself — there is no central `logger.add` call, so adding sinks/rotation should be done in one place (ideally `main.py`) rather than scattered across modules.
- For persistent audit trails, use the ModerationLog/VideoModerationLog repositories instead of relying on console logs.