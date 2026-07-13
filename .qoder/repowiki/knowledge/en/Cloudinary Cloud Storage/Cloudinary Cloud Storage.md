---
kind: external_dependency
name: Cloudinary Cloud Storage
slug: cloudinary
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

### Cloudinary SaaS image hosting
- Role: Optional remote image upload/delete service, configured via `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` env vars.
- Usage model: currently unused by core moderation endpoints — present as an optional storage backend alongside local filesystem uploads.
- Verify exact upload options and public_id format against official docs.