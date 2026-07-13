# Performance & Caching

<cite>
**Referenced Files in This Document**
- [redis.py](file://backend/app/core/redis.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [celery_app.py](file://backend/app/core/celery_app.py)
- [tasks.py](file://backend/app/tasks.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [video_moderation.py](file://backend/app/services/video_moderation.py)
- [moderate.py](file://backend/app/api/moderate.py)
- [database.py](file://backend/app/core/database.py)
- [config.py](file://backend/app/core/config.py)
- [ARCHITECTURE.md](file://ARCHITECTURE.md)
- [speed_test.py](file://backend/speed_test.py)
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
This document provides comprehensive performance documentation for the OmniShield platform with a focus on caching strategies, background processing, and optimization techniques. It details:
- SHA256-based image deduplication that eliminates duplicate processing by computing content hashes and storing results in Redis with configurable TTL policies.
- The Redis caching layer implementation including connection pooling, cache invalidation strategies, and memory optimization techniques.
- Celery background task processing for batch operations, queue management, error handling, and progress tracking for long-running jobs.
- Performance benchmarks and throughput optimization strategies, including GPU auto-detection with CUDA acceleration, lazy model loading, and async/await patterns across the stack.
- Scalability considerations such as horizontal scaling, database connection pooling, read replica support, and CDN integration for static assets.
- Monitoring and profiling tools to identify bottlenecks and detect performance regressions.

## Project Structure
The backend is organized into core services (caching, AI moderation, video moderation), API endpoints, background tasks, and configuration. Key performance-related modules include:
- Redis client initialization and availability checks
- Image hashing and caching service
- Celery app and background tasks
- Multi-model moderation orchestrator with parallel execution
- Video moderation pipeline using async frame sampling and concurrent moderation
- Database session management with async engines and connection pooling
- Configuration settings for cache TTLs, GPU usage, and rate limits

```mermaid
graph TB
subgraph "API Layer"
A["FastAPI Router<br/>/moderate/image, /moderate/batch"]
end
subgraph "Services"
B["AI Moderation<br/>Lazy-loaded NudeDetector"]
C["Multi-Model Moderation<br/>Parallel exec + ThreadPoolExecutor"]
D["Video Moderation<br/>Async frame sampling + gather"]
E["Hash Cache Service<br/>SHA256 + Redis"]
end
subgraph "Background Processing"
F["Celery App<br/>Broker/Backend via Redis"]
G["Batch Task<br/>Download, cache check, moderate, log"]
end
subgraph "Data Stores"
H["Redis<br/>Cache + Broker"]
I["PostgreSQL<br/>Async Engine + Pool"]
end
A --> E
A --> B
A --> C
A --> D
A --> F
F --> G
E --> H
B --> H
C --> H
D --> I
G --> I
A --> I
```

**Diagram sources**
- [moderate.py](file://backend/app/api/moderate.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [video_moderation.py](file://backend/app/services/video_moderation.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [celery_app.py](file://backend/app/core/celery_app.py)
- [tasks.py](file://backend/app/tasks.py)
- [database.py](file://backend/app/core/database.py)
- [redis.py](file://backend/app/core/redis.py)

**Section sources**
- [moderate.py](file://backend/app/api/moderate.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [video_moderation.py](file://backend/app/services/video_moderation.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [celery_app.py](file://backend/app/core/celery_app.py)
- [tasks.py](file://backend/app/tasks.py)
- [database.py](file://backend/app/core/database.py)
- [redis.py](file://backend/app/core/redis.py)

## Core Components
- Redis Client Initialization: Provides a shared Redis client with short connect timeout and graceful degradation if unavailable.
- Image Hash Cache: Computes SHA256 checksums per file path, uses Redis keys prefixed with content hash, stores JSON-encoded results with TTL, and avoids caching error outputs.
- Celery App: Initializes Celery with broker and result backend configured via settings; imports tasks module for discovery.
- Batch Task: Downloads images from URLs, checks cache by SHA256, runs inference on cache miss, persists logs, and cleans up temp files.
- AI Moderation: Lazy-loads NudeDetector, applies close-up padding and fallback heuristics, maps detections to risk levels and recommended actions.
- Multi-Model Moderation: Orchestrates NSFW, violence (CLIP), weapons (YOLOv8), faces (MTCNN), and text (OCR + profanity) detectors concurrently using asyncio.gather and ThreadPoolExecutor; includes GPU auto-detection and lazy loading.
- Video Moderation: Samples frames at configurable intervals, converts BGR to RGB, runs multi-model moderation concurrently, aggregates flags, and persists results.
- Database Layer: Async engine with pool_pre_ping and session generators for FastAPI routes; sync engine used for migrations and CLI.

**Section sources**
- [redis.py](file://backend/app/core/redis.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [celery_app.py](file://backend/app/core/celery_app.py)
- [tasks.py](file://backend/app/tasks.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [video_moderation.py](file://backend/app/services/video_moderation.py)
- [database.py](file://backend/app/core/database.py)

## Architecture Overview
The system integrates an API layer with caching, background processing, and AI inference services. Requests are validated and routed to either real-time moderation or asynchronous batch/video pipelines. Results are cached in Redis and persisted to PostgreSQL. Background workers process queued tasks using Celery with Redis as both broker and result backend.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "FastAPI Router"
participant Cache as "ImageHashCache"
participant AI as "AI Moderation"
participant MM as "Multi-Model Moderation"
participant DB as "PostgreSQL"
participant Redis as "Redis"
participant Celery as "Celery Worker"
Client->>API : POST /moderate/image
API->>Cache : get(file_path)
alt Cache Hit
Cache-->>API : Cached result
API->>DB : Create log entry
API-->>Client : Response (cached=true)
else Cache Miss
API->>AI : moderate_image_file(file_path)
AI-->>API : Result
API->>Cache : set(file_path, result, ttl)
API->>DB : Create log entry
API-->>Client : Response (cached=false)
end
Client->>API : POST /moderate/batch {urls}
API->>Celery : send_task("app.tasks.moderate_batch", args=[user_id, urls])
Celery->>Cache : get(temp_file)
alt Cache Hit
Cache-->>Celery : Cached result
Celery->>DB : Log entry
else Cache Miss
Celery->>AI : moderate_image_file(temp_file)
AI-->>Celery : Result
Celery->>Cache : set(temp_file, result)
Celery->>DB : Log entry
end
Celery-->>API : Task result stored in backend
```

**Diagram sources**
- [moderate.py](file://backend/app/api/moderate.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [tasks.py](file://backend/app/tasks.py)
- [celery_app.py](file://backend/app/core/celery_app.py)
- [database.py](file://backend/app/core/database.py)
- [redis.py](file://backend/app/core/redis.py)

## Detailed Component Analysis

### SHA256-Based Image Deduplication and Redis Caching
- Content Hashing: Each uploaded image is hashed using SHA256 over fixed-size blocks to compute a stable key independent of filename.
- Cache Keys: Keys are prefixed with a namespace and include the computed hash to ensure uniqueness across different files.
- TTL Policy: Default TTL is configurable via settings; successful results are cached while errors are intentionally skipped to avoid propagating failures.
- Graceful Degradation: If Redis is unavailable, requests proceed without caching, ensuring resilience.

```mermaid
flowchart TD
Start(["Request Received"]) --> ComputeHash["Compute SHA256 of file"]
ComputeHash --> CheckRedis{"Redis available?"}
CheckRedis --> |No| SkipCache["Skip cache lookup"]
CheckRedis --> |Yes| GetKey["Get cache key 'image_cache:{hash}'"]
GetKey --> HasResult{"Cached result exists?"}
HasResult --> |Yes| ReturnCached["Return cached result"]
HasResult --> |No| RunInference["Run AI moderation"]
RunInference --> SetTTL["Set result in Redis with TTL"]
SetTTL --> PersistDB["Persist to DB"]
SkipCache --> RunInference
ReturnCached --> PersistDB
PersistDB --> End(["Response Sent"])
```

**Diagram sources**
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [redis.py](file://backend/app/core/redis.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [moderate.py](file://backend/app/api/moderate.py)

**Section sources**
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [redis.py](file://backend/app/core/redis.py)
- [config.py](file://backend/app/core/config.py)

### Redis Caching Layer Implementation
- Connection Pooling: Uses redis-py’s default connection pooling with a low socket connect timeout to prevent blocking on network issues.
- Availability Flag: Maintains a global flag indicating whether Redis is reachable; all cache operations guard against unavailability.
- Memory Optimization: Avoids caching error responses; uses compact JSON serialization and reasonable TTLs to control memory footprint.
- Invalidation Strategy: TTL-based expiration; no explicit invalidation logic is implemented beyond time-based expiry.

**Section sources**
- [redis.py](file://backend/app/core/redis.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [config.py](file://backend/app/core/config.py)

### Celery Background Task Processing
- Queue Management: Tasks are sent via Celery with Redis as both broker and result backend; task serializer and accept content are configured to JSON.
- Batch Workflow: Downloads remote images, checks cache by SHA256, runs inference on cache miss, caches results, and persists logs.
- Error Handling: Individual URL processing exceptions are caught and logged; temp files are cleaned up in finally blocks.
- Progress Tracking: Clients poll task status via AsyncResult; results are stored in the backend for retrieval.

```mermaid
sequenceDiagram
participant API as "FastAPI Router"
participant Celery as "Celery App"
participant Worker as "Worker Process"
participant Cache as "ImageHashCache"
participant AI as "AI Moderation"
participant DB as "PostgreSQL"
API->>Celery : send_task("app.tasks.moderate_batch")
Celery-->>Worker : Dispatch task
loop For each URL
Worker->>Worker : Download image to temp file
Worker->>Cache : get(temp_file)
alt Cache Hit
Cache-->>Worker : Cached result
Worker->>DB : Insert log entry
else Cache Miss
Worker->>AI : moderate_image_file(temp_file)
AI-->>Worker : Result
Worker->>Cache : set(temp_file, result)
Worker->>DB : Insert log entry
end
end
Worker-->>API : Task completed (result stored in backend)
```

**Diagram sources**
- [celery_app.py](file://backend/app/core/celery_app.py)
- [tasks.py](file://backend/app/tasks.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [moderate.py](file://backend/app/api/moderate.py)

**Section sources**
- [celery_app.py](file://backend/app/core/celery_app.py)
- [tasks.py](file://backend/app/tasks.py)
- [moderate.py](file://backend/app/api/moderate.py)

### Multi-Model Moderation and Parallel Execution
- Model Orchestration: Combines NSFW detection (NudeNet), violence detection (CLIP), weapon detection (YOLOv8), face detection (MTCNN), and text moderation (PaddleOCR + Profanity).
- Concurrency: Uses asyncio.gather with ThreadPoolExecutor to run CPU/GPU-bound detectors concurrently, maximizing throughput.
- GPU Auto-Detection: Models check torch.cuda.is_available() and move to GPU when possible; CLIP and MTCNN explicitly target CUDA devices.
- Lazy Loading: Detectors are initialized on first use to reduce startup latency and memory footprint.
- Aggregation: Results are aggregated with risk scoring and confidence calibration; professional portrait override reduces false positives for single-face scenarios.

```mermaid
classDiagram
class ModerationResult {
+string status
+float confidence
+string risk_level
+string recommended_action
+string reason
+dict categories
+list detected_labels
+list bounding_boxes
+float processing_time
+dict model_versions
}
class MultiModelModeration {
+async moderate_image_comprehensive_async(image_path, enable_*)
-_run_detector_async(detector_func, image_path, category_name, executor)
+detect_nsfw(image_path)
+detect_violence(image_path)
+detect_weapons(image_path)
+detect_faces(image_path)
+detect_text(image_path)
}
class LazyLoaders {
+get_nsfw_detector()
+get_violence_detector()
+get_weapon_detector()
+get_face_detector()
+get_ocr_reader()
+get_profanity_filter()
}
MultiModelModeration --> ModerationResult : "returns"
MultiModelModeration --> LazyLoaders : "uses"
```

**Diagram sources**
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)

**Section sources**
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)

### Video Moderation Pipeline
- Frame Sampling: Extracts one frame per second based on FPS and interval configuration; converts BGR to RGB for model compatibility.
- Concurrent Moderation: Queues each sampled frame for multi-model moderation and executes them concurrently via asyncio.gather.
- Aggregation: Collects frame-level flags, determines overall status/risk/confidence, and persists summary telemetry.
- Persistence: Updates job status transitions (pending -> processing -> complete/fail) and writes frame flags for auditability.

```mermaid
flowchart TD
Start(["Video Upload"]) --> Validate["Validate container signatures"]
Validate --> CreateJob["Create pending job record"]
CreateJob --> OpenCap["Open video with OpenCV"]
OpenCap --> SampleFrames["Sample frames at interval"]
SampleFrames --> ConvertRGB["Convert BGR to RGB"]
ConvertRGB --> ModerateFrame["Run multi-model moderation (async)"]
ModerateFrame --> Aggregate["Aggregate flags and metrics"]
Aggregate --> Persist["Persist frame flags and summary"]
Persist --> End(["Complete/Fail job"])
```

**Diagram sources**
- [video_moderation.py](file://backend/app/services/video_moderation.py)
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [moderate.py](file://backend/app/api/moderate.py)

**Section sources**
- [video_moderation.py](file://backend/app/services/video_moderation.py)
- [moderate.py](file://backend/app/api/moderate.py)

## Dependency Analysis
The following diagram shows key dependencies between components involved in performance-critical paths:

```mermaid
graph TB
Config["Settings (config.py)"]
RedisInit["Redis Client (redis.py)"]
CacheSvc["ImageHashCache (hash_cache.py)"]
API["Moderation Router (moderate.py)"]
AI["AI Moderation (ai_moderation.py)"]
MM["Multi-Model Moderation (multi_model_moderation.py)"]
CeleryApp["Celery App (celery_app.py)"]
Tasks["Batch Task (tasks.py)"]
DB["Database (database.py)"]
Config --> RedisInit
Config --> API
Config --> CeleryApp
RedisInit --> CacheSvc
API --> CacheSvc
API --> AI
API --> MM
API --> DB
CeleryApp --> Tasks
Tasks --> CacheSvc
Tasks --> AI
Tasks --> DB
MM --> AI
```

**Diagram sources**
- [config.py](file://backend/app/core/config.py)
- [redis.py](file://backend/app/core/redis.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [moderate.py](file://backend/app/api/moderate.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [celery_app.py](file://backend/app/core/celery_app.py)
- [tasks.py](file://backend/app/tasks.py)
- [database.py](file://backend/app/core/database.py)

**Section sources**
- [config.py](file://backend/app/core/config.py)
- [redis.py](file://backend/app/core/redis.py)
- [hash_cache.py](file://backend/app/services/hash_cache.py)
- [moderate.py](file://backend/app/api/moderate.py)
- [ai_moderation.py](file://backend/app/services/ai_moderation.py)
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [celery_app.py](file://backend/app/core/celery_app.py)
- [tasks.py](file://backend/app/tasks.py)
- [database.py](file://backend/app/core/database.py)

## Performance Considerations
- Cache Hit Performance: Cache lookups bypass expensive inference; typical Redis GET/SET operations are sub-millisecond under normal conditions.
- Model Inference Times: Single-image inference times vary by model complexity and hardware; comprehensive multi-model runs aggregate multiple detectors concurrently.
- Throughput Optimization:
  - Parallel execution via asyncio.gather and ThreadPoolExecutor maximizes concurrency for CPU/GPU-bound tasks.
  - Lazy model loading reduces startup overhead and memory footprint.
  - GPU auto-detection moves models to CUDA when available, improving inference speed.
  - Async/await patterns keep I/O non-blocking across API routes and background tasks.
- Database Connection Pooling: Async engine uses pool_pre_ping and session generators to efficiently manage connections.
- Horizontal Scaling: Multiple API pods behind a load balancer, Redis cluster, and auto-scaling Celery workers improve throughput.
- Read Replicas: PostgreSQL replicas can offload analytics queries to reduce primary load.
- CDN Integration: Static assets served via CDN reduce origin load and improve frontend performance.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Redis Unavailable:
  - Symptom: Cache misses despite repeated uploads; graceful degradation activates.
  - Action: Verify REDIS_URL connectivity; inspect redis_available flag and logs.
- Batch Task Failures:
  - Symptom: Some URLs fail while others succeed; temp files not cleaned.
  - Action: Check worker logs for download/inference errors; ensure cleanup in finally blocks.
- High Inference Latency:
  - Symptom: Slow responses for comprehensive moderation.
  - Action: Confirm GPU availability; tune max_workers; consider enabling only necessary detectors.
- Database Connection Issues:
  - Symptom: Timeouts or connection pool exhaustion.
  - Action: Review pool sizes and pool_pre_ping; monitor active connections and query durations.

**Section sources**
- [redis.py](file://backend/app/core/redis.py)
- [tasks.py](file://backend/app/tasks.py)
- [multi_model_moderation.py](file://backend/app/services/multi_model_moderation.py)
- [database.py](file://backend/app/core/database.py)

## Conclusion
OmniShield’s performance architecture leverages SHA256-based deduplication, Redis caching with TTL policies, and Celery-backed background processing to deliver scalable, high-throughput moderation. Parallel execution, lazy model loading, and GPU acceleration further optimize inference times. With robust connection pooling, horizontal scaling, and monitoring hooks, the platform maintains reliability and responsiveness under varying loads.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Benchmarks and Measurement
- Speed Test Utility: A simple script measures single-image scan time using NudeDetector to establish baseline inference latency.
- Frontend Metrics: The UI displays average latency for cache-miss model runs, aiding in operational visibility.

**Section sources**
- [speed_test.py](file://backend/speed_test.py)
- [ARCHITECTURE.md](file://ARCHITECTURE.md)

### Monitoring and Alerting
- Key Metrics: HTTP request duration, AI inference duration, database connection pool state, Redis cache hits/misses, and business moderation counts.
- Alert Rules: High error rates, slow inference thresholds, and database down alerts help detect regressions early.

**Section sources**
- [ARCHITECTURE.md](file://ARCHITECTURE.md)