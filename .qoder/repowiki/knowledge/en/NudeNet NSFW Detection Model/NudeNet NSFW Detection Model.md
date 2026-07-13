---
kind: external_dependency
name: NudeNet NSFW Detection Model
slug: nudenet
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

### NudeNet v3.4.2 (ONNX Runtime)
- Role: Primary NSFW/explicit-content detector in the 6-model ensemble.
- Usage model: invoked via `moderate_image_file` from `ai_moderation.py` inside the async pipeline; bounding boxes are coerced to int lists before serialization.
- Verify exact API/params against official docs.