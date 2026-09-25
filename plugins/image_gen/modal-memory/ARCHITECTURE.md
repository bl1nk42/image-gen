# Modal Memory Plugin Architecture

The plugin follows Hermes guidance: capabilities that require binary processing, API credentials, streaming, or exact execution remain tools; repeatable procedures are skills; user-invoked workflows are commands; multi-step judgment is an agent; hooks observe and guard the lifecycle.

| Component | Responsibility | Hermes surface |
|---|---|---|
| Modal provider | Generate/edit/upscale through Modal + ComfyUI | `ImageGenProvider` |
| `analyze_image`, `queue_*`, `cache_*`, HF sync | Binary/API/queue operations | Tools |
| prompt preparation, dataset curation, style learning, deployment | Repeatable instructions + scripts | Skills |
| create-from-template, sync-dataset, inspect-cache | Explicit user workflows | Commands |
| style-curator | Multi-step review of references, votes, and embeddings | Agent |
| post-tool observer | Metrics, cache metadata, quality flags | Plugin hook |
| `model-catalog.json` | Local catalog, compatible with Hermes catalog metadata | Data |

The local catalog mirrors Hermes's versioned manifest idea (`version`, `updated_at`, `metadata`, `providers`, `models`) while retaining a provider-specific `image_models` block. Unknown metadata is intentionally preserved so the catalog can be published or merged later.

## Data flow

```text
image_generate -> provider -> cache lookup -> Modal queue -> ComfyUI -> image cache
                                      |                         |
                                      +-> job status             +-> HF dataset/model repo
analyze_image -> vision endpoint -> analysis cache -> registry/style learner
```

Every mutating operation is idempotent where possible, records a correlation ID, and returns a JSON string with `status`, `error_type`, `message`, and `remediation` on failure.
