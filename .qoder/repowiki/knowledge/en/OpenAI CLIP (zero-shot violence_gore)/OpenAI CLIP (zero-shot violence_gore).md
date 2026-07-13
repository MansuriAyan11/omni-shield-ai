---
kind: external_dependency
name: OpenAI CLIP (zero-shot violence/gore)
slug: openai-clip
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

### openai/clip-vit-base-patch32
- Role: Violence and gore classification via zero-shot prompts through `transformers.CLIPModel` + `CLIPProcessor`.
- Usage model: image tensor is processed through CLIPProcessor then scored against violence-related text prompts; result merged into the categories dict.
- Verify exact prompt/template and label mapping against official docs.