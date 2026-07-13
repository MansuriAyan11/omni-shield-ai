# Development Workflow

<cite>
**Referenced Files in This Document**
- [README.md](file://nudenet_project/README.md)
- [QUICK_START.md](file://nudenet_project/QUICK_START.md)
- [docker-compose.yml](file://nudenet_project/docker-compose.yml)
- [setup_and_run.ps1](file://nudenet_project/setup_and_run.ps1)
- [start_servers.ps1](file://nudenet_project/start_servers.ps1)
- [backend/app/core/config.py](file://nudenet_project/backend/app/core/config.py)
- [backend/create_tables.py](file://nudenet_project/backend/create_tables.py)
- [backend/requirements.txt](file://nudenet_project/backend/requirements.txt)
- [frontend/package.json](file://nudenet_project/frontend/package.json)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document provides a complete local development workflow for the OmniShield platform, covering environment setup (Python 3.12+, Node.js 20+, PostgreSQL 15, Redis), Docker Compose orchestration, local server startup via PowerShell scripts, hot reload configuration for backend and frontend, database initialization, debugging techniques, environment variable configuration, API key generation, AI model loading optimization, and troubleshooting common issues such as port conflicts, database connectivity, CORS, memory management, Docker container problems, dependency resolution, and performance bottlenecks.

## Project Structure
The repository is organized into:
- Backend: FastAPI application with core services, models, repositories, schemas, and tasks
- Frontend: React + Vite application with TypeScript
- Orchestration: Docker Compose for multi-service development
- Scripts: PowerShell automation for setup and server management

```mermaid
graph TB
subgraph "Backend"
B_App["FastAPI App<br/>app/main.py"]
B_Config["Settings<br/>app/core/config.py"]
B_DB["DB Init Script<br/>create_tables.py"]
B_Req["Python Deps<br/>requirements.txt"]
end
subgraph "Frontend"
F_Pkg["Vite + React<br/>package.json"]
end
subgraph "Orchestration"
DC["Docker Compose<br/>docker-compose.yml"]
end
subgraph "Scripts"
S_Run["Setup & Run<br/>setup_and_run.ps1"]
S_Start["Start Servers<br/>start_servers.ps1"]
end
S_Run --> B_DB
S_Run --> B_App
S_Run --> F_Pkg
S_Start --> B_App
S_Start --> F_Pkg
DC --> B_App
DC --> F_Pkg
```

**Diagram sources**
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)
- [setup_and_run.ps1:1-117](file://nudenet_project/setup_and_run.ps1#L1-L117)
- [start_servers.ps1:1-93](file://nudenet_project/start_servers.ps1#L1-L93)
- [backend/app/core/config.py:1-148](file://nudenet_project/backend/app/core/config.py#L1-L148)
- [backend/create_tables.py:1-19](file://nudenet_project/backend/create_tables.py#L1-L19)
- [backend/requirements.txt:1-142](file://nudenet_project/backend/requirements.txt#L1-L142)
- [frontend/package.json:1-38](file://nudenet_project/frontend/package.json#L1-L38)

**Section sources**
- [README.md:139-172](file://nudenet_project/README.md#L139-L172)

## Core Components
- Backend runtime and dependencies:
  - Python virtual environment and requirements are managed under backend/requirements.txt. The app uses FastAPI and Uvicorn for async HTTP serving.
- Frontend runtime:
  - React + Vite with TypeScript; dev server script defined in package.json.
- Configuration:
  - Centralized settings loaded from .env via pydantic-settings, including DB URL, Redis URLs, CORS origins, and feature toggles for AI models.
- Database initialization:
  - create_tables.py creates tables using SQLAlchemy Base metadata without Alembic.

Key operational notes:
- Local backend hot reload is enabled via Uvicorn’s --reload flag in PowerShell scripts.
- Frontend hot reload is provided by Vite’s dev server.
- Docker Compose defines PostgreSQL 15 and Redis 7 services, plus backend and Celery worker containers.

**Section sources**
- [backend/requirements.txt:1-142](file://nudenet_project/backend/requirements.txt#L1-L142)
- [frontend/package.json:1-38](file://nudenet_project/frontend/package.json#L1-L38)
- [backend/app/core/config.py:1-148](file://nudenet_project/backend/app/core/config.py#L1-L148)
- [backend/create_tables.py:1-19](file://nudenet_project/backend/create_tables.py#L1-L19)

## Architecture Overview
Local development architecture includes:
- FastAPI backend on port 8000
- React/Vite frontend on port 3000
- PostgreSQL 15 on port 5432
- Redis 7 on port 6379
- Optional Celery worker for background tasks

```mermaid
graph TB
Client["Browser / Dev Tools"] --> FE["React + Vite<br/>localhost:3000"]
FE --> BE["FastAPI + Uvicorn<br/>localhost:8000"]
BE --> PG["PostgreSQL 15<br/>localhost:5432"]
BE --> RD["Redis 7<br/>localhost:6379"]
BE --> Celery["Celery Worker<br/>optional"]
```

**Diagram sources**
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)
- [start_servers.ps1:1-93](file://nudenet_project/start_servers.ps1#L1-L93)

## Detailed Component Analysis

### Environment Setup and Prerequisites
- Python 3.12+
  - Create and activate a virtual environment in backend/.
  - Install dependencies from backend/requirements.txt.
- Node.js 20+
  - Install dependencies in frontend/ using npm.
- PostgreSQL 15
  - Use Docker Compose service or install locally; ensure connection string matches DATABASE_URL.
- Redis 7
  - Use Docker Compose service or install locally; ensure REDIS_URL matches.

Recommended approach:
- Use Docker Compose to run PostgreSQL and Redis automatically.
- For local dev, start backend and frontend servers with PowerShell scripts.

**Section sources**
- [README.md:176-240](file://nudenet_project/README.md#L176-L240)
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)

### Docker Compose Orchestration
Services:
- postgres: PostgreSQL 15 with healthcheck and persistent volume
- redis: Redis 7 with AOF persistence and healthcheck
- backend: FastAPI app with environment variables for DB and Redis
- celery: Background worker using Redis broker/result backend
- frontend: React build served via nginx (production-oriented)

Notes:
- Backend depends_on ensures DB and Redis are healthy before starting.
- Ports exposed: 5432 (postgres), 6379 (redis), 8000 (backend), 80 (frontend).

**Section sources**
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)

### Local Development Server Startup (PowerShell)
Two primary scripts:
- setup_and_run.ps1: Initializes DB tables, stops existing servers, starts backend and frontend in separate terminals
- start_servers.ps1: Starts backend and frontend, checks ports, installs frontend deps if missing

Hot reload:
- Backend: Uvicorn --reload enabled
- Frontend: Vite dev server provides hot module replacement

Access points:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

```mermaid
sequenceDiagram
participant Dev as "Developer"
participant PS as "PowerShell Script"
participant BE as "Backend (Uvicorn)"
participant FE as "Frontend (Vite)"
participant DB as "PostgreSQL"
participant RC as "Redis"
Dev->>PS : Run setup_and_run.ps1
PS->>BE : Start uvicorn --reload
PS->>FE : Start vite dev
BE->>DB : Connect via DATABASE_URL
BE->>RC : Connect via REDIS_URL
Dev->>FE : Open http : //localhost : 3000
FE->>BE : API calls to http : //localhost : 8000
```

**Diagram sources**
- [setup_and_run.ps1:1-117](file://nudenet_project/setup_and_run.ps1#L1-L117)
- [start_servers.ps1:1-93](file://nudenet_project/start_servers.ps1#L1-L93)
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)

**Section sources**
- [setup_and_run.ps1:1-117](file://nudenet_project/setup_and_run.ps1#L1-L117)
- [start_servers.ps1:1-93](file://nudenet_project/start_servers.ps1#L1-L93)
- [QUICK_START.md:64-98](file://nudenet_project/QUICK_START.md#L64-L98)

### Database Initialization and Seeding
- Tables creation:
  - Use backend/create_tables.py to initialize schema via SQLAlchemy Base metadata.
- Default storage:
  - SQLite file moderation.db when DATABASE_URL points to sqlite+aiosqlite.
- Seeding sample data:
  - No explicit seed script found; consider adding a seeding routine that inserts test users and logs after table creation.

```mermaid
flowchart TD
Start(["Init DB"]) --> CheckEnv["Check DATABASE_URL"]
CheckEnv --> IsSQLite{"sqlite?"}
IsSQLite --> |Yes| CreateTables["Run create_tables.py"]
IsSQLite --> |No| EnsurePG["Ensure PostgreSQL running"]
EnsurePG --> CreateTables
CreateTables --> Ready["Tables ready"]
```

**Diagram sources**
- [backend/create_tables.py:1-19](file://nudenet_project/backend/create_tables.py#L1-L19)
- [backend/app/core/config.py:30-42](file://nudenet_project/backend/app/core/config.py#L30-L42)

**Section sources**
- [backend/create_tables.py:1-19](file://nudenet_project/backend/create_tables.py#L1-L19)
- [QUICK_START.md:31-50](file://nudenet_project/QUICK_START.md#L31-L50)

### Environment Variables and Configuration
Centralized settings via pydantic-settings:
- ENVIRONMENT: development/staging/production
- JWT_SECRET and JWT_ALGORITHM for authentication
- DATABASE_URL: supports sqlite and postgresql+asyncpg conversion
- REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
- CORS_ORIGINS: wildcard or comma-separated list
- Feature toggles: ENABLE_NSFW_DETECTION, ENABLE_VIOLENCE_DETECTION, etc.
- GPU support: USE_GPU, GPU_DEVICE_ID

Validation and warnings:
- Production validation enforces changing default JWT_SECRET
- Warnings issued for permissive CORS in production

Example keys to configure locally:
- DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/moderation_db
- REDIS_URL=redis://localhost:6379/0
- CELERY_BROKER_URL=redis://localhost:6379/1
- CELERY_RESULT_BACKEND=redis://localhost:6379/1
- CORS_ORIGINS=http://localhost:3000
- USE_GPU=false (set true only if GPU available)

**Section sources**
- [backend/app/core/config.py:1-148](file://nudenet_project/backend/app/core/config.py#L1-L148)

### API Key Generation for Testing
- Generate an account via the frontend registration flow.
- Use the backend API to generate an API key (requires JWT bearer token).
- Use the returned key in requests via X-API-Key header.

References:
- README documents API key generation and usage endpoints.

**Section sources**
- [README.md:267-281](file://nudenet_project/README.md#L267-L281)

### Hot Reload Configuration
- Backend:
  - Uvicorn --reload enables automatic restart on code changes.
- Frontend:
  - Vite dev server provides HMR out-of-the-box.

Operational tips:
- Keep both terminals open for live updates.
- Avoid saving large files during active inference to reduce reload overhead.

**Section sources**
- [setup_and_run.ps1:64-76](file://nudenet_project/setup_and_run.ps1#L64-L76)
- [start_servers.ps1:37-53](file://nudenet_project/start_servers.ps1#L37-L53)
- [frontend/package.json:6-11](file://nudenet_project/frontend/package.json#L6-L11)

### Debugging Techniques
- VS Code launch configurations:
  - Configure a Python debug launch targeting uvicorn app.main:app with --reload disabled for stable breakpoints.
  - Attach to the running backend process if needed.
- Python debugger:
  - Use pdb or breakpoint() in critical paths (e.g., moderation pipeline).
- Browser developer tools:
  - Network tab to inspect API calls and responses.
  - Console for frontend errors and Axios request details.
- Log analysis:
  - Backend logs in terminal; enable structured logging via loguru if configured.
  - Frontend logs in browser console.

[No sources needed since this section provides general guidance]

### AI Model Loading Optimization
- Lazy loading:
  - Models load on-demand to reduce startup time.
- GPU acceleration:
  - Set USE_GPU=true if CUDA-capable hardware is available.
- Quantization:
  - INT8 inference can improve speed where supported.
- Caching:
  - SHA256-based image deduplication reduces redundant processing.

**Section sources**
- [README.md:490-508](file://nudenet_project/README.md#L490-L508)
- [backend/app/core/config.py:70-82](file://nudenet_project/backend/app/core/config.py#L70-L82)

## Dependency Analysis
Key dependencies:
- Backend:
  - FastAPI, Uvicorn, SQLAlchemy, asyncpg, Pydantic v2, Redis, Celery, NudeNet, ONNX Runtime, Transformers, Ultralytics YOLOv8, PaddleOCR, MTCNN
- Frontend:
  - React, Vite, TypeScript, Tailwind CSS, Recharts, Axios

```mermaid
graph LR
Req["requirements.txt"] --> FastAPI["FastAPI"]
Req --> Uvicorn["Uvicorn"]
Req --> SQLAlchemy["SQLAlchemy"]
Req --> AsyncPG["asyncpg"]
Req --> Redis["Redis"]
Req --> Celery["Celery"]
Req --> NudeNet["NudeNet"]
Req --> ONNX["ONNX Runtime"]
Req --> Torch["PyTorch"]
Req --> Transformers["Transformers"]
Req --> YOLO["Ultralytics YOLOv8"]
Req --> OCR["PaddleOCR"]
Req --> MTCNN["MTCNN"]
Pkg["frontend/package.json"] --> React["React"]
Pkg --> Vite["Vite"]
Pkg --> TS["TypeScript"]
Pkg --> Tailwind["Tailwind CSS"]
Pkg --> Recharts["Recharts"]
Pkg --> Axios["Axios"]
```

**Diagram sources**
- [backend/requirements.txt:1-142](file://nudenet_project/backend/requirements.txt#L1-L142)
- [frontend/package.json:1-38](file://nudenet_project/frontend/package.json#L1-L38)

**Section sources**
- [backend/requirements.txt:1-142](file://nudenet_project/backend/requirements.txt#L1-L142)
- [frontend/package.json:1-38](file://nudenet_project/frontend/package.json#L1-L38)

## Performance Considerations
- Cache hits are extremely fast due to SHA256 hashing.
- Multi-model ensemble adds latency; consider enabling only required models via feature toggles.
- Use GPU acceleration when available.
- Monitor Redis cache hit rates and Celery queue lengths.
- Tune batch sizes and thresholds based on workload.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide

Common issues and resolutions:
- Port conflicts:
  - Backend (8000) and Frontend (3000) may be occupied; use PowerShell commands to identify and terminate processes.
- Virtual environment issues:
  - Recreate venv and reinstall dependencies if corrupted.
- Node modules issues:
  - Remove node_modules and lockfile, then reinstall.
- Database issues:
  - For SQLite, delete moderation.db and recreate tables; for PostgreSQL, verify connection string and service availability.
- Docker container issues:
  - Check healthchecks and logs; ensure volumes persist data; confirm network connectivity between services.
- Dependency resolution problems:
  - Pin versions in requirements.txt; use consistent Python version; clear pip caches if necessary.
- CORS configuration:
  - Set CORS_ORIGINS to include http://localhost:3000 for local development.
- Memory management for large AI models:
  - Disable unused models; set USE_GPU appropriately; monitor process memory; consider quantization.

**Section sources**
- [QUICK_START.md:107-148](file://nudenet_project/QUICK_START.md#L107-L148)
- [docker-compose.yml:16-39](file://nudenet_project/docker-compose.yml#L16-L39)
- [backend/app/core/config.py:88-99](file://nudenet_project/backend/app/core/config.py#L88-L99)

## Conclusion
This guide consolidates the full local development workflow for OmniShield, from environment setup through Docker Compose orchestration, server startup, debugging, configuration, and troubleshooting. By following these steps, developers can efficiently iterate on both backend and frontend components while leveraging caching, optional GPU acceleration, and robust observability practices.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Quick Commands Reference
- Initialize DB tables:
  - backend/create_tables.py
- Start servers:
  - setup_and_run.ps1 or start_servers.ps1
- Access UI and API:
  - Frontend: http://localhost:3000
  - Backend: http://localhost:8000
  - Docs: http://localhost:8000/docs

**Section sources**
- [backend/create_tables.py:1-19](file://nudenet_project/backend/create_tables.py#L1-L19)
- [setup_and_run.ps1:104-117](file://nudenet_project/setup_and_run.ps1#L104-L117)
- [start_servers.ps1:81-93](file://nudenet_project/start_servers.ps1#L81-L93)
- [QUICK_START.md:90-98](file://nudenet_project/QUICK_START.md#L90-L98)