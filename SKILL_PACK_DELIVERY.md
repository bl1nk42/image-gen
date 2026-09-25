# Visual Production Skill Pack — Delivery Note

## Purpose

The previous implementation treated specialist skills as short descriptions. This revision turns them into an operational workflow layer for the Modal + ComfyUI image system. Each skill now defines activation scope, routing decisions, execution gates, quality checks, privacy behavior, and references that can be loaded only when needed. Exact API, binary, queue, cache, and storage operations remain tools; the skills explain when and why those tools are used.

## Included skills

| Skill | Operational value |
|---|---|
| `visual-production-router` | Selects the smallest complete workflow and composes specialist skills for mixed requests. |
| `image-generation` | Routes models, normalizes prompts, checks cache, queues batches, handles references, and applies a quality gate. |
| `photo-restoration` | Uses preservation-first restoration with identity, composition, text, and historical-period checks. |
| `nothing-design` | Applies explicit Nothing-inspired typography, monochrome hierarchy, spacing, tokens, components, and anti-pattern checks. |
| `memory-recall` | Retrieves prior decisions with source, date, confidence, conflict handling, and current-state verification. |
| `prompt-engineer` | Defines contracts, test sets, evaluation scores, versioning, and rollback behavior for prompts. |
| `character-story-video` | Establishes an anchor character, plans beats, generates references, handles dependent scenes, and records continuity. |
| `video-generator` | Uses phase gates, clip blueprints, 16:9/9:16 rules, reference-first execution, narration budgets, and audio mixing. |
| `meme-generator` | Uses deterministic Memegen.link templates, correct encoding, short copy, preview, and route separation from generative artwork. |

## Supporting resources

The pack includes reference files for prompt contracts, model routing, quality gates, queue behavior, restoration profiles, preservation checks, Nothing tokens/components, memory contracts, prompt patterns, structured output, video blueprints, continuity, and meme template mapping. The references are linked from their owning skill and are intentionally one level deep for progressive disclosure.

The pack also includes a `style-curator` agent for evidence-based style learning, commands for prompt preview, image status, and dataset sync, and metadata-only hooks for audit events. Private prompts and image bytes are not written to the audit log.

## Integration

`install.py --claude` copies the complete Claude plugin directory. The Hermes provider remains under `plugins/image_gen/modal-memory`. The plugin manifest is version `1.0.0`, and the Hermes manifest describes the expanded generation, restoration, analysis, cache, queue, memory, dataset, and Hugging Face scope.

## Validation

The following checks passed:

- Skill pack validator: all nine skills valid; no missing referenced resources.
- Standard `quick_validate.py`: initialized router skill valid.
- Modal project verification: catalog, tools, Claude manifest, and smoke tests passed.
- Python `compileall`: application, Modal backend, plugins, Claude plugin, and installer compiled successfully.
- Modal backend import: `MODAL_IMPORT_OK`.
- One-command installer layout: Hermes provider, Claude skill index, photo restoration skill, video skill, and manifest copied successfully.

## Known boundary

Actual Modal GPU inference, ComfyUI execution, Hugging Face upload, and video-provider calls still require the user's credentials, model weights, workflow JSON, and provider endpoints. The local validation intentionally tests contracts and failure paths without pretending that external GPU inference has occurred.
