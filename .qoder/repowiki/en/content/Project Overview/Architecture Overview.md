# Architecture Overview

<cite>
**Referenced Files in This Document**
- [README.md](file://nudenet_project/README.md)
- [ARCHITECTURE.md](file://nudenet_project/ARCHITECTURE.md)
- [docker-compose.yml](file://nudenet_project/docker-compose.yml)
- [DEPLOYMENT.md](file://nudenet_project/DEPLOYMENT.md)
- [backend/app/main.py](file://nudenet_project/backend/app/main.py)
- [backend/app/core/config.py](file://nudenet_project/backend/app/core/config.py)
- [backend/app/api/moderate.py](file://nudenet_project/backend/app/api/moderate.py)
- [backend/app/services/multi_model_moderation.py](file://nudenet_project/backend/app/services/multi_model_moderation.py)
- [backend/requirements.txt](file://nudenet_project/backend/requirements.txt)
- [frontend-nextjs-backup/package.json](file://nudenet_project/frontend-nextjs-backup/package.json)
</cite>

## Table of Contents
1. Introduction
2. Project Structure
3. Core Components
4. Architecture Overview
5. Detailed Component Analysis
6. Dependency Analysis
7. Performance Considerations
8. Troubleshooting Guide
9. Conclusion
10. Appendices

## Introduction
OmniShield is a production-ready, multi-tenant AI content moderation platform that combines six specialized models (NSFW, violence, weapons, faces, text, gore) to deliver comprehensive safety analysis. The system uses a microservices-style architecture with FastAPI for the backend API, Next.js for the frontend dashboard, PostgreSQL for persistence, Redis for caching and task brokering, Celery workers for background processing, and nginx as an edge load balancer and reverse proxy. It emphasizes high performance through SHA256-based image deduplication and caching, parallel model inference via async + thread pools, and robust security layers including JWT, API keys, rate limiting, and input validation.

## Project Structure
The repository organizes code into clear layers:
- Backend (FastAPI): API endpoints, core configuration, database access, services, repositories, schemas, and tasks.
- Frontend (Next.js): Dashboard UI and API client.
- Infrastructure: Docker Compose for local orchestration; deployment manifests and scripts for production and Kubernetes.

```mermaid
graph TB
subgraph "Backend"
A["FastAPI App<br/>main.py"]
B["Config<br/>core/config.py"]
C["Moderation API<br/>api/moderate.py"]
D["Multi-Model Service<br/>services/multi_model_moderation.py"]
end
subgraph "Infra"
E["PostgreSQL"]
F["Redis"]
G["Celery Worker"]
H["nginx"]
end
subgraph "Frontend"
I["Next.js App"]
end
I --> H
H --> A
A --> B
A --> C
C --> D
C --> E
C --> F
C --> G
```

**Diagram sources**
- [backend/app/main.py:1-126](file://nudenet_project/backend/app/main.py#L1-L126)
- [backend/app/core/config.py:1-148](file://nudenet_project/backend/app/core/config.py#L1-L148)
- [backend/app/api/moderate.py:1-615](file://nudenet_project/backend/app/api/moderate.py#L1-L615)
- [backend/app/services/multi_model_moderation.py:1-777](file://nudenet_project/backend/app/services/multi_model_moderation.py#L1-L777)
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)

**Section sources**
- [README.md:140-172](file://nudenet_project/README.md#L140-L172)
- [ARCHITECTURE.md:60-86](file://nudenet_project/ARCHITECTURE.md#L60-L86)

## Core Components
- API Server (FastAPI): Handles authentication, request validation, routing, caching, orchestration of AI pipeline, and response serialization.
- Multi-Model AI Pipeline: Executes NSFW (NudeNet), Violence (CLIP), Weapons (YOLOv8), Faces (MTCNN), Text (PaddleOCR + Profanity), and Gore (CLIP) detectors in parallel with ensemble aggregation.
- Cache Layer (Redis): Stores SHA256-based image results and supports rate limiting and session storage.
- Database (PostgreSQL): Persists users, API keys, moderation logs, and video moderation jobs.
- Background Workers (Celery): Processes batch moderation and scheduled tasks asynchronously.
- Edge Proxy (nginx): Load balances, terminates TLS, enforces security headers, and routes traffic to backend and frontend.

**Section sources**
- [backend/app/main.py:1-126](file://nudenet_project/backend/app/main.py#L1-L126)
- [backend/app/core/config.py:1-148](file://nudenet_project/backend/app/core/config.py#L1-L148)
- [backend/app/api/moderate.py:1-615](file://nudenet_project/backend/app/api/moderate.py#L1-L615)
- [backend/app/services/multi_model_moderation.py:1-777](file://nudenet_project/backend/app/services/multi_model_moderation.py#L1-L777)
- [ARCHITECTURE.md:181-222](file://nudenet_project/ARCHITECTURE.md#L181-L222)
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)

## Architecture Overview
High-level flow from client to response:
- Client requests are routed by nginx to the FastAPI backend.
- Authentication validates JWT or API key.
- Request body is validated (magic bytes, size limits).
- Cache lookup by SHA256 returns cached results when available.
- On cache miss, the multi-model pipeline runs all enabled detectors in parallel.
- Results are aggregated via ensemble voting and risk scoring.
- Responses are cached and logged to PostgreSQL.
- Batch jobs are queued to Celery for asynchronous processing.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Nginx as "nginx"
participant API as "FastAPI"
participant Auth as "Auth Middleware"
participant Cache as "Redis"
participant AI as "Multi-Model Service"
participant DB as "PostgreSQL"
participant Worker as "Celery Worker"
Client->>Nginx : HTTPS request
Nginx->>API : Route to /api/v1/*
API->>Auth : Validate JWT/API Key
Auth-->>API : Authorized
API->>Cache : Check SHA256 result
alt Cache Hit
Cache-->>API : Cached moderation result
API-->>Client : Return result (cached=true)
else Cache Miss
API->>AI : Run parallel detectors
AI-->>API : Aggregated result
API->>Cache : Store result (TTL)
API->>DB : Persist log
API-->>Client : Return result (cached=false)
end
Note over API,Worker : Batch jobs use Celery queue
```

**Diagram sources**
- [backend/app/api/moderate.py:223-378](file://nudenet_project/backend/app/api/moderate.py#L223-L378)
- [backend/app/api/moderate.py:446-615](file://nudenet_project/backend/app/api/moderate.py#L446-L615)
- [backend/app/services/multi_model_moderation.py:532-732](file://nudenet_project/backend/app/services/multi_model_moderation.py#L532-L732)
- [ARCHITECTURE.md:224-305](file://nudenet_project/ARCHITECTURE.md#L224-L305)

## Detailed Component Analysis

### API Server (FastAPI)
- Registers routers under /api/v1, adds CORS and security headers, mounts Prometheus metrics if enabled, and provides health endpoints.
- Enforces environment-specific behavior (e.g., strict CORS in production).

```mermaid
classDiagram
class FastAPI_App {
+title
+version
+docs_url
+redoc_url
+on_event("startup")
+on_event("shutdown")
+middleware("http") add_security_headers()
+include_router(auth)
+include_router(keys)
+include_router(moderate)
+include_router(analytics)
}
```

**Diagram sources**
- [backend/app/main.py:1-126](file://nudenet_project/backend/app/main.py#L1-L126)

**Section sources**
- [backend/app/main.py:1-126](file://nudenet_project/backend/app/main.py#L1-L126)

### Configuration and Security
- Centralized settings loaded from environment with Pydantic Settings.
- Validates environment, JWT secret strength in production, and parses CORS origins.
- Provides URLs for async database connections, Redis, Celery broker/backend, and feature toggles for each detector.

```mermaid
flowchart TD
Start(["App Startup"]) --> LoadCfg["Load Settings (.env)"]
LoadCfg --> ValidateEnv{"ENVIRONMENT valid?"}
ValidateEnv --> |No| Error["Raise ValueError"]
ValidateEnv --> |Yes| ValidateJWT{"Production & strong JWT?"}
ValidateJWT --> |No| Error
ValidateJWT --> |Yes| ParseCORS["Parse CORS_ORIGINS"]
ParseCORS --> Ready["Ready to serve"]
```

**Diagram sources**
- [backend/app/core/config.py:1-148](file://nudenet_project/backend/app/core/config.py#L1-L148)

**Section sources**
- [backend/app/core/config.py:1-148](file://nudenet_project/backend/app/core/config.py#L1-L148)

### Moderation Endpoints
- Single image moderation: validates file extension and magic bytes, checks cache, runs NudeNet on miss, caches result, persists log.
- Comprehensive moderation: enables/disables detectors via query params, runs parallel multi-model pipeline, aggregates results, persists enhanced fields.
- Video moderation: queues job, returns status URL, polls for completion.
- Batch moderation: enqueues Celery task, returns task ID for polling.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "Moderation Router"
participant Cache as "Redis"
participant Service as "Multi-Model Service"
participant Repo as "Log Repository"
Client->>API : POST /moderate/image/comprehensive
API->>API : Validate extension + magic bytes
API->>Cache : Lookup by SHA256 (+ config suffix)
alt Cache Hit
Cache-->>API : Result
API-->>Client : Return cached result
else Cache Miss
API->>Service : moderate_image_result_dict_async(...)
Service-->>API : Aggregated categories + metadata
API->>Repo : create_log(..., model_results, versions, face_count, text)
API-->>Client : Return enriched result
end
```

**Diagram sources**
- [backend/app/api/moderate.py:446-615](file://nudenet_project/backend/app/api/moderate.py#L446-L615)
- [backend/app/services/multi_model_moderation.py:532-732](file://nudenet_project/backend/app/services/multi_model_moderation.py#L532-L732)

**Section sources**
- [backend/app/api/moderate.py:223-378](file://nudenet_project/backend/app/api/moderate.py#L223-L378)
- [backend/app/api/moderate.py:446-615](file://nudenet_project/backend/app/api/moderate.py#L446-L615)

### Multi-Model AI Pipeline and Ensemble Voting
- Detectors:
  - NSFW: NudeNet v3.4.2 (ONNX Runtime)
  - Violence: CLIP zero-shot classification
  - Weapons: YOLOv8 object detection
  - Faces: MTCNN face detection
  - Text: PaddleOCR + profanity filter
  - Gore: CLIP zero-shot classification
- Parallel execution: asyncio.gather with ThreadPoolExecutor to run CPU/GPU-bound inference concurrently.
- Ensemble strategy:
  - Aggregate labels and bounding boxes across models.
  - Map per-model risk levels to numeric scores and compute aggregate risk score.
  - Decision thresholds: critical/high -> block; medium -> quarantine; low -> allow.
  - Confidence calibration: max confidence among unsafe categories or average for safe.
  - Professional portrait override: reduces false positives for single-face images without weapons and low violence probability.

```mermaid
flowchart TD
A["Start"] --> B["Run detectors in parallel"]
B --> C{"Any unsafe?"}
C --> |Yes| D["Aggregate labels/boxes"]
D --> E["Compute aggregate risk score"]
E --> F{"Score >= 80?"}
F --> |Yes| G["Decision: block (critical)"]
F --> |No| H{"Score >= 50?"}
H --> |Yes| I["Decision: block (high)"]
H --> |No| J{"Score >= 25?"}
J --> |Yes| K["Decision: quarantine (medium)"]
J --> |No| L["Decision: allow (low)"]
C --> |No| M["Average confidence -> allow (low)"]
```

**Diagram sources**
- [backend/app/services/multi_model_moderation.py:532-732](file://nudenet_project/backend/app/services/multi_model_moderation.py#L532-L732)

**Section sources**
- [backend/app/services/multi_model_moderation.py:1-777](file://nudenet_project/backend/app/services/multi_model_moderation.py#L1-L777)

### Background Processing (Celery)
- Batch moderation endpoint enqueues tasks using Celery app.
- Task status polling endpoint queries AsyncResult.
- Workers consume tasks from Redis broker and persist results.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "Batch Endpoint"
participant Broker as "Redis (Celery)"
participant Worker as "Celery Worker"
participant DB as "PostgreSQL"
Client->>API : POST /moderate/batch {urls}
API->>Broker : send_task("app.tasks.moderate_batch", args=[user_id, urls])
API-->>Client : {task_id, status : PENDING}
Client->>API : GET /moderate/tasks/{task_id}
API->>Broker : AsyncResult(task_id)
Broker-->>API : Status/Result
API-->>Client : {status, result?}
Worker->>Broker : Dequeue task
Worker->>DB : Persist results
Worker->>Broker : Mark SUCCESS
```

**Diagram sources**
- [backend/app/api/moderate.py:380-444](file://nudenet_project/backend/app/api/moderate.py#L380-L444)

**Section sources**
- [backend/app/api/moderate.py:380-444](file://nudenet_project/backend/app/api/moderate.py#L380-L444)

### Frontend (Next.js)
- Next.js 16 application with React 19, TypeScript, Tailwind CSS, Recharts, Axios, and Framer Motion.
- Serves dashboard pages and interacts with the FastAPI backend.

```mermaid
graph TB
FE["Next.js App<br/>package.json"] --> API["FastAPI Backend"]
```

**Diagram sources**
- [frontend-nextjs-backup/package.json:1-32](file://nudenet_project/frontend-nextjs-backup/package.json#L1-L32)

**Section sources**
- [frontend-nextjs-backup/package.json:1-32](file://nudenet_project/frontend-nextjs-backup/package.json#L1-L32)

## Dependency Analysis
Key runtime dependencies include FastAPI, Uvicorn, SQLAlchemy async, asyncpg, Redis, Celery, Pydantic v2, and AI libraries (NudeNet, Transformers/CLIP, Ultralytics YOLOv8, facenet-pytorch/MTCNN, PaddleOCR).

```mermaid
graph LR
FastAPI["FastAPI 0.137"] --> Uvicorn["Uvicorn 0.49"]
FastAPI --> Pydantic["Pydantic v2"]
FastAPI --> SQLAlchemy["SQLAlchemy 2.0 (async)"]
SQLAlchemy --> AsyncPG["asyncpg"]
FastAPI --> Redis["redis 5.0"]
FastAPI --> Celery["celery 5.4"]
FastAPI --> NudeNet["nudenet 3.4.2"]
FastAPI --> Transformers["transformers 5.13"]
FastAPI --> Ultralytics["ultralytics 8.4"]
FastAPI --> Facenet["facenet-pytorch 2.5"]
FastAPI --> PaddleOCR["paddleocr 3.4"]
```

**Diagram sources**
- [backend/requirements.txt:1-142](file://nudenet_project/backend/requirements.txt#L1-L142)

**Section sources**
- [backend/requirements.txt:1-142](file://nudenet_project/backend/requirements.txt#L1-L142)

## Performance Considerations
- Caching: SHA256-based image deduplication with Redis TTL reduces repeated inference cost.
- Parallelism: Async/await combined with ThreadPoolExecutor executes multiple models concurrently.
- Model optimization: Lazy loading, GPU auto-detection, and quantization options improve throughput.
- Scalability: Horizontal scaling of API pods, read replicas for analytics, and auto-scaling workers.
- Observability: Prometheus metrics, structured logging, and alerting rules for error rates and slow inference.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and diagnostics:
- Database connectivity: verify connection strings and service health.
- Redis connectivity: ping Redis and inspect stats.
- Model loading failures: ensure model artifacts exist and test loader functions.
- High memory usage: monitor container stats and scale workers down if needed.
- Slow API responses: analyze DB activity, Redis hit rate, and API logs.

**Section sources**
- [DEPLOYMENT.md:718-800](file://nudenet_project/DEPLOYMENT.md#L718-L800)

## Conclusion
OmniShield’s architecture delivers a scalable, secure, and high-performance moderation platform by combining a modular FastAPI backend, a modern Next.js frontend, robust caching and queuing with Redis and Celery, persistent storage in PostgreSQL, and an edge proxy with nginx. The ensemble voting system integrates six specialized AI models in parallel to produce accurate, explainable decisions while maintaining low latency through caching and efficient resource utilization.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Technology Stack and Version Compatibility Matrix
- Backend: FastAPI 0.137, Uvicorn 0.49, Python 3.12+, SQLAlchemy 2.0 (async), asyncpg, Pydantic v2.
- Database: PostgreSQL 15.
- Cache/Queue: Redis 7, Celery 5.4.
- AI Models: NudeNet 3.4.2 (ONNX), Transformers 5.13 (CLIP), Ultralytics 8.4 (YOLOv8), facenet-pytorch 2.5 (MTCNN), PaddleOCR 3.4.
- Frontend: Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, Recharts 3.9, Axios, Framer Motion 12.
- Infra: Docker, Docker Compose, nginx, Prometheus, Grafana.

**Section sources**
- [README.md:621-657](file://nudenet_project/README.md#L621-L657)
- [backend/requirements.txt:1-142](file://nudenet_project/backend/requirements.txt#L1-L142)
- [frontend-nextjs-backup/package.json:1-32](file://nudenet_project/frontend-nextjs-backup/package.json#L1-L32)

### Deployment Topology
- Local: docker-compose orchestrates PostgreSQL, Redis, backend, worker, and frontend containers.
- Production: nginx terminates TLS and load balances to backend/frontend; optional Cloudflare WAF/CDN upstream; Kubernetes manifests provided for stateful and stateless components.

```mermaid
graph TB
Internet["Internet"] --> CF["CloudFlare (optional)"]
CF --> LB["nginx (TLS termination)"]
LB --> FE["Next.js Pods"]
LB --> BE["FastAPI Pods"]
BE --> DB["PostgreSQL Primary"]
BE --> R["Redis Cluster"]
BE --> Q["Celery Workers"]
```

**Diagram sources**
- [ARCHITECTURE.md:620-651](file://nudenet_project/ARCHITECTURE.md#L620-L651)
- [DEPLOYMENT.md:249-351](file://nudenet_project/DEPLOYMENT.md#L249-L351)
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)

**Section sources**
- [docker-compose.yml:1-108](file://nudenet_project/docker-compose.yml#L1-L108)
- [DEPLOYMENT.md:149-412](file://nudenet_project/DEPLOYMENT.md#L149-L412)
- [ARCHITECTURE.md:620-651](file://nudenet_project/ARCHITECTURE.md#L620-L651)