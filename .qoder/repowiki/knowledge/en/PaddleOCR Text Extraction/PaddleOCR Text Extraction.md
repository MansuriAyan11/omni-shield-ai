---
kind: external_dependency
name: PaddleOCR Text Extraction
slug: paddleocr
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

- Role: Text extraction for the "text" moderation category, combined with a profanity filter.
- Usage model: extracted text is passed through `better-profanity` and flagged accordingly.
- Verify exact language/model selection flags against official docs.