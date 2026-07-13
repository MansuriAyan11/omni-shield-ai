---
kind: error_handling
name: FastAPI HTTPException-based error handling with per-route try/except
category: error_handling
scope:
    - '**'
source_files:
    - backend/app/main.py
    - backend/app/core/security.py
    - backend/app/api/auth.py
    - backend/app/api/analytics.py
    - backend/app/api/keys.py
    - backend/app/api/moderate.py
---

The OmniShield backend uses FastAPI's built-in `HTTPException` as the primary error-propagation mechanism. There is no centralized custom exception hierarchy, no global `@app.exception_handler` registrations, and no sentinel-error pattern — errors are raised directly from route handlers and dependencies and bubble up to FastAPI's default JSON error formatter.

**Where it lives**
- Route-level: every endpoint in `backend/app/api/*.py` wraps its body in `try / except Exception` blocks and converts caught exceptions into `HTTPException(status_code=..., detail=...)`. See `auth.py`, `analytics.py`, `keys.py`, and the large `moderate.py` (image/video upload, batch/Celery, comprehensive multi-model).
- Authentication/authorization: `core/security.py` defines reusable auth dependencies (`get_current_user`, `get_api_key_user`, `get_current_client`, `require_role`) that raise `HTTPException(401)` for bad tokens/missing credentials and `HTTPException(403)` for inactive accounts or insufficient roles.
- Global middleware: `main.py` registers only CORS and a security-headers middleware; there is no global exception handler, so FastAPI's default `RequestValidationError` → 422 response remains unchanged.

**Conventions observed**
- Validation failures are surfaced via explicit `raise HTTPException(status_code=status.HTTP_4XX_BAD_REQUEST, detail="...")` inside each route (e.g., missing filename, unsupported extension, empty file, size exceeded). No Pydantic `Field(...)` validation is used on request bodies, so client input is not auto-validated by FastAPI.
- Business/logic errors use distinct status codes consistently: 400 for bad input, 401 for missing/invalid JWT or API key, 403 for inactive user or unauthorized access, 404 for missing resources, 413 for oversized uploads, 500 for unexpected failures.
- Unexpected exceptions are always logged through `loguru.logger.exception(...)` before being re-wrapped as a 500 `HTTPException`; the raw traceback is never returned to the client.
- File-upload routes follow a shared cleanup pattern: they keep a local `file_path` variable, catch both `HTTPException` (re-raise) and generic `Exception`, delete the temp file in both branches, and always close the uploaded file in a `finally` block.
- Async background work (Celery tasks, video moderation jobs) returns 202 Accepted with a job/status URL; task-status queries return 500 if Celery is unreachable.

**What is missing**
- No custom exception classes (no `NotFoundError`, `ValidationError`, etc.) — all errors are ad-hoc `HTTPException` instances.
- No global exception handler to normalize error responses (e.g., wrap every response in `{"success": bool, "error": {...}}`).
- No structured error-code enum or machine-readable error identifiers; clients must parse free-form `detail` strings.
- Frontend code (`frontend/src/lib/axios.ts`) does not appear to implement a unified Axios interceptor for error normalization, so error presentation is likely scattered across components.