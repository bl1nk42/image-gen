# Model Routing

| Request | Required capability | Route |
|---|---|---|
| New image | text | Modal provider default model |
| Fast batch | text + queue | `queue_image` with independent jobs |
| Edit/reference | image/edit | only model with `supports.edit=true` |
| Image caption/metadata | vision/analyze | `analyze_image` |
| Exact chart/diagram | deterministic | plotting/Mermaid, not diffusion |
| Classic meme | template text | meme-generator skill |
| Character sequence | identity + sequential references | character-story-video skill |
| Video | keyframes + temporal model | video-generator skill |

Always prefer the cached model catalog. If a model is unavailable, report the fallback rather than silently changing the intended modality.
