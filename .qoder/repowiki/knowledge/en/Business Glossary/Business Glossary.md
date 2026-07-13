---
kind: business_term
name: Business Glossary
category: business_term
scope:
    - '**'
---

### OmniShield
- Definition：Internal product name for this enterprise-grade AI content moderation platform (project title, README header, config `PROJECT_NAME`).

### video moderation job
- Definition：An asynchronous moderation request submitted via `POST /api/v1/moderate/video`; returns HTTP 202 with a `job_id` and `status_url` that clients poll to retrieve aggregated results after frames are sampled and classified.
- Aliases：video job

### VideoModerationLog
- Definition：SQLAlchemy ORM model representing one video moderation job record, including overall status, risk level, confidence, sampling metadata, and a relationship to per-frame flag rows.
- Aliases：video log

### VideoFrameFlag
- Definition：Child record linking a specific timestamped frame within a `VideoModerationLog` to its detected violation category, confidence, and labels.
- Aliases：frame flag

### overall_status
- Definition：Aggregated safety verdict for a video moderation job (`safe` or `unsafe`), derived from any unsafe frame across all sampled timestamps.
- Aliases：overall decision

### flag_category
- Definition：The moderation category (nsfw, violence, weapons, faces, text, or aggregate) associated with a single flagged frame row.
- Aliases：frame category

### comprehensive moderation
- Definition：The multi-model ensemble endpoint `POST /api/v1/moderate/image/comprehensive` that runs NSFW, violence, weapons, faces, and text detectors concurrently and merges their outputs into a single response.
- Aliases：multi-model moderation、ensemble moderation

### SHA256 caching
- Definition：Image deduplication strategy where the first N bytes of an uploaded image are hashed to a SHA256 key stored in Redis; subsequent identical images return cached results in <2ms without re-running models.
- Aliases：image hash cache
