---
kind: dependency_management
name: Dual-Stack Dependency Management (pip + npm)
category: dependency_management
scope:
    - '**'
source_files:
    - nudenet_project/backend/requirements.txt
    - nudenet_project/backend/pyproject.toml
    - nudenet_project/backend/Dockerfile
    - nudenet_project/frontend/package.json
    - nudenet_project/frontend/package-lock.json
    - nudenet_project/docker-compose.yml
---

The repository manages dependencies for two independent stacks — a Python FastAPI backend and a React/TypeScript frontend — using each stack's native package manager. There is no monorepo-level lockfile or unified tooling; the two sides are versioned and installed separately.

**Python backend (`backend/`)**
- **Manifest**: `requirements.txt` pins every transitive dependency to an exact version (e.g. `fastapi==0.137.0`, `torch==2.12.1`, `nudenet==3.4.2`). This is the single source of truth for production installs.
- **Lockfile**: No `requirements.lock` / `uv.lock` / `poetry.lock`; reproducibility relies on the fully-pinned `requirements.txt`.
- **Build-time extras**: `Dockerfile` installs system packages (`build-essential`, `libgl1-mesa-glx`, `libglib2.0-0`) via `apt-get` before `pip install -r requirements.txt`, and pre-caches the NudeNet ONNX model at build time with a one-shot Python import so runtime startup is faster.
- **Virtual environment**: A local `venv/` directory exists under both `backend/` and the repo root, but it is not committed (gitignored). The Docker image is the canonical reproducible environment.
- **pyproject.toml**: Present only for tool configuration (Black, Ruff, mypy, pytest, coverage); it does not declare project dependencies, so `pip` ignores it during install.
- **Private registries / vendoring**: None detected — all packages resolve from PyPI. No `.pip/pip.conf`, `Pipfile`, `poetry.lock`, or vendored `vendor/` directory.

**Frontend (`frontend/`)**
- **Manifest**: `package.json` declares runtime `dependencies` (React, Axios, Recharts, TanStack Query, etc.) and `devDependencies` (Vite, TypeScript, Tailwind, ESLint) using caret ranges (`^x.y.z`).
- **Lockfile**: `package-lock.json` (lockfileVersion 3) is committed alongside `package.json`, pinning every resolved sub-dependency and its integrity hash. This guarantees deterministic builds across machines.
- **Install strategy**: Standard `npm ci` / `npm install` against the public npm registry; no private registry, `.npmrc`, or vendored `node_modules` in git.
- **Alternative Next.js frontend**: A parallel `frontend-nextjs-backup/` directory contains its own `package.json` + `package-lock.json`, independently versioned and unrelated to the Vite-based frontend.

**Container orchestration**
- `docker-compose.yml` defines four services (`postgres`, `redis`, `backend`, `celery`, plus a legacy `frontend` service pointing at a non-existent `./frontend-react` context). Each container pulls official images from Docker Hub; no custom base images or private registry mirrors are configured.

**Conventions & rules developers should follow**
- Backend: always pin versions in `backend/requirements.txt` and never rely on `pyproject.toml` for dependency declarations. Add new wheels by appending a pinned line rather than running `pip freeze` over a mutable venv.
- Frontend: keep `package.json` ranges sensible and commit `package-lock.json` after every change; do not edit the lockfile by hand.
- Do not commit `venv/` or `node_modules/`; use the Docker images as the single source of truth for CI and production.
- System-level OS dependencies required by ML libraries (OpenCV, NudeNet) must be added in `backend/Dockerfile` alongside their Python counterparts.