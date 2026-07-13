---
kind: build_system
name: Dockerized Multi-Service Build & CI/CD Pipeline
category: build_system
scope:
    - '**'
source_files:
    - nudenet_project/docker-compose.yml
    - nudenet_project/backend/Dockerfile
    - nudenet_project/frontend/Dockerfile
    - nudenet_project/.github/workflows/ci.yml
    - nudenet_project/.github/workflows/deploy.yml
    - nudenet_project/backend/pyproject.toml
    - nudenet_project/frontend/package.json
---

The OmniShield project uses a Docker-first, GitHub Actions-driven build and deployment system spanning two independent services (FastAPI backend + Vite/React frontend) orchestrated via `docker-compose.yml`.

**Build tools and packaging**
- Backend: Python 3.12 with `requirements.txt` for dependency pinning; image built from `python:3.12-slim`, installs system libs (`libgl1-mesa-glx`, `libglib2.0-0`) needed by OpenCV/NudeNet, pre-caches the NudeNet ONNX model at build time, then runs `uvicorn app.main:app`. A separate Celery worker container reuses the same image with `celery -A app.core.celery_app worker --loglevel=info`.
- Frontend: Node 18 Alpine multi-stage build — `node:18-alpine AS builder` runs `npm ci --only=production` + `npm run build` (Vite), then `nginx:alpine` serves the static `/app/dist` output via a custom `nginx.conf`. The root `docker-compose.yml` references a `frontend-react` directory that is not present in this branch, so the active compose file is out of sync with the current `frontend/` layout.
- Database migrations are managed by Alembic (`alembic.ini`, `backend/migrations/versions/`); production deploys run `alembic upgrade head` after pulling images.

**CI/CD pipeline (GitHub Actions)**
Two workflow files coexist:
- `.github/workflows/ci.yml` — the primary pipeline triggered on push/PR to `main` and `develop`. It runs parallel jobs per service:
  - Backend linting (Black check, Ruff, mypy), testing (pytest with async mode against ephemeral Postgres 15 + Redis 7 containers), security scans (Bandit JSON report, Safety against `requirements.txt`).
  - Frontend linting (ESLint, `tsc --noEmit`), test build, and a Docker build-only job using `docker/build-push-action` with GHA cache.
  - Trivy filesystem scans producing SARIF uploaded to GitHub Security.
  - Staging deploy (`develop` branch): builds/pushes `:staging` + commit-sha tags to Docker Hub, SSH-deploys via `appleboy/ssh-action` to `/opt/omnishield`, runs `docker-compose pull` + `up -d --no-deps --build backend frontend worker`, then migrates DB.
  - Production deploy (`main` branch or `refs/tags/v*` tag): same flow but tags `:latest`, `:<version>`, `<sha>`; also creates a GitHub Release when a tag is pushed.
- `.github/workflows/deploy.yml` — an alternate/supplementary pipeline targeting Vercel (frontend) and Railway (backend) deployments, plus Docker Hub pushes. This file references `frontend-react` and Node 18/Python 3.11, indicating it lags behind the current toolchain.

**Local development orchestration**
- `docker-compose.yml` defines four services: `postgres` (Alpine, healthcheck via `pg_isready`), `redis` (appendonly enabled, healthcheck via `redis-cli ping`), `backend` (ports 8000, volumes for uploads/dataset), `celery` worker, and a `frontend` service pointing at a missing `./frontend-react` context. All services share a bridge network `omnishield-network`; persistent data lives in named volumes `postgres_data` and `redis_data`.
- Several PowerShell helpers exist at repo root (`setup_and_run.ps1`, `start_servers.ps1`, `restart_servers.ps1`, `check_servers.ps1`, `migrate_frontend.ps1`) for Windows developers to spin up services locally without Docker Compose.

**Quality gates and conventions**
- Python tooling is configured in `backend/pyproject.toml`: Black (100-col lines, py312 target), Ruff with E/W/F/I/C/B/UP rule sets, mypy with strict-equality and explicit optional checks, pytest with `asyncio_mode=auto`, coverage scoped to `app/` excluding tests/migrations/venv.
- Frontend scripts in `frontend/package.json`: `dev` (Vite), `build` (TypeScript compile then Vite build), `lint` (ESLint with zero-warn threshold).
- Versioning strategy: Docker images tagged with `:staging`, `:latest`, `<git-sha>`, and optionally `<semver>` extracted from `refs/tags/v*` during production deploy.
- Secrets required by CI: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `STAGING_HOST/USER/SSH_KEY`, `PRODUCTION_HOST/USER/SSH_KEY`, `VERCEL_TOKEN/ORG_ID/PROJECT_ID`, `RAILWAY_TOKEN`.