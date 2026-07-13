---
kind: configuration_system
name: Pydantic Settings-Based Environment Configuration
category: configuration_system
scope:
    - '**'
source_files:
    - nudenet_project/backend/app/core/config.py
    - nudenet_project/backend/.env
    - nudenet_project/.env.example
    - nudenet_project/frontend/.env
    - nudenet_project/frontend/.env.example
    - nudenet_project/backend/app/core/database.py
    - nudenet_project/backend/app/core/redis.py
---

The OmniShield platform uses a centralized, type-safe configuration system built on pydantic_settings.BaseSettings. All runtime configuration is loaded from environment variables and .env files into a single Settings singleton consumed across the backend.

Loading mechanism
- backend/app/core/config.py defines a Settings(BaseSettings) class with typed fields, defaults, validators, and computed properties.
- The class-level model_config points to .env in the backend root (env_file=".env", extra="ignore").
- A module-level settings = Settings() instance is imported wherever needed (APIs, database, Redis, rate limiter, etc.).
- Frontend config is separate: Vite reads frontend/.env for VITE_API_URL at build time.

Environment variable categories
- Application identity: PROJECT_NAME, VERSION, ENVIRONMENT (validated enum: development/staging/production).
- Security: JWT_SECRET, JWT_ALGORITHM, token expiry; production validator rejects default secrets.
- Database: DATABASE_URL (SQLite dev default), with an ASYNC_DATABASE_URL property that auto-converts postgresql:// to postgresql+asyncpg://.
- Cache & queue: REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND, plus cache TTLs.
- Uploads: directories, allowed extensions/content types, size/batch limits.
- AI feature flags: per-model toggles (ENABLE_NSFW_DETECTION, ENABLE_VIOLENCE_DETECTION, ...) and GPU switches.
- Rate limiting: per-minute caps for default/admin users.
- CORS: comma-separated string parsed into a list via a property.
- Optional integrations: OAuth2 client IDs/secrets, Cloudinary credentials, AWS S3 endpoints, Sentry DSN, Prometheus toggle.

Validation and guards
- @field_validator("ENVIRONMENT") enforces allowed values.
- @field_validator("JWT_SECRET") raises when ENVIRONMENT=production and the secret still contains the default placeholder.
- Startup warning emitted if CORS_ORIGINS=* while ENVIRONMENT=production.

Consumption pattern
- app.core.database imports settings to build sync/async SQLAlchemy engines.
- app.core.redis connects using settings.REDIS_URL with graceful degradation on failure.
- app.api.moderate, app.core.advanced_rate_limit, and other modules import from app.core.config import settings and read values directly — no dependency injection of the settings object.

File layout
- Backend env template: nudenet_project/.env.example (PostgreSQL + full checklist).
- Backend runtime env: nudenet_project/backend/.env (SQLite dev defaults).
- Frontend env: nudenet_project/frontend/.env and frontend/.env.example (only VITE_API_URL).

Rules developers should follow
1. Add new configuration by declaring a typed field with a sensible default in backend/app/core/config.py; it will be picked up automatically from .env or any matching environment variable.
2. Use Optional[...] for non-required integrations (OAuth, Cloudinary, S3, Sentry) so the app runs without them.
3. Put validation logic in @field_validator decorators rather than ad-hoc checks scattered across modules.
4. Keep secrets out of source control — commit only .env.example; never commit backend/.env.
5. For frontend-only URLs, use VITE_* variables in frontend/.env; they are not available to the Python backend.