---
kind: external_dependency
name: YOLOv8 Object Detection (weapons)
slug: ultralytics-yolov8
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

### Ultralytics YOLOv8 (nano model)
- Role: Weapon/object detection for the "weapons" category.
- Usage model: runs inference on each frame; detections are folded into the categories dict with labels like KNIFE/GUN.
- Verify exact class names and confidence thresholds against official docs.