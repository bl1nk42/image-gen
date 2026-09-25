# Visual Production Skills Index

This plugin is a workflow system, not a flat collection of prompts. The router selects the smallest complete workflow and composes specialist skills only when needed.

| Skill | Use it for | Produces |
|---|---|---|
| `visual-production-router` | Ambiguous or multi-modal requests | route, assumptions, composed plan |
| `image-generation` | New/edit images and batches | prompt, image, cache/job manifest, quality result |
| `photo-restoration` | Restoration and preservation | restoration brief, edited image, preservation gate |
| `nothing-design` | Explicit Nothing design | theme tokens, hierarchy, implementation/generation direction |
| `memory-recall` | Prior decisions/preferences | traceable memory summary with confidence |
| `prompt-engineer` | Prompt reliability | versioned prompt, test cases, score, rollback |
| `character-story-video` | Character-consistent multi-scene stories | anchor, scene plan, refs, clips, continuity record |
| `video-generator` | General video production | phase-gated blueprint, keyframes, clips, audio mix, manifest |
| `meme-generator` | Classic captioned memes | template URL/file, encoded text, preview |

Skills are deliberately separate from tools. Tools perform exact binary/API/queue/storage operations; skills explain when, why, and in what order to call them.
