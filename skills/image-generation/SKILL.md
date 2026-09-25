---
name: image-generation
description: Production image generation through Modal + ComfyUI or configured providers. Use when creating, editing, analyzing, caching, queueing, or registering images, including text-bearing visuals, references, style consistency, and multi-image batches.
---
# Image Generation

## Mission
Deliver a usable image, not merely a prompt. Choose the lowest-cost route that satisfies the request, preserve user constraints, make the executed prompt inspectable, and avoid duplicate generation.

## Route first
1. Classify the job: new image, edit, restoration, precise layout, meme, character continuity, or video reference.
2. Choose the provider/model from `model-catalog.json`; check `supports`, aspect ratios, edit capability, and queue availability.
3. If the request is a diagram or numeric chart, do not use generative imagery as the source of truth: use Mermaid or deterministic plotting.
4. If an image is supplied, call `analyze_image` before editing unless the requested change is unambiguous and reversible.
5. Normalize prompt with `prepare_prompt_tool`, then check cache using the full request signature.

## Prompt contract
Structure the prompt as: purpose/medium, subject, composition, lighting/material, exact text, constraints, avoid list. Preserve names, numbers, dates, and requested language exactly. Separate subject facts from learned style. Apply style suffix only after the subject is complete. Negative prompts must name bare concepts, not sentences such as “do not”.

## Execution
- One image: call the provider after cache lookup.
- Multiple independent images: use `queue_image`; retain every `job_id`; use `get_job` rather than resubmitting.
- Dependent sequence: execute sequentially and pass the actual prior output as reference.
- Edit: verify `supports.edit`; describe only the requested change and explicit preservation constraints.
- After success: return image, model, executed prompt, aspect ratio, cache state, job ID if any, and registration status.

## Quality gate
Pass only if the output has the requested subject, composition/aspect, text or no-text constraint, reference fidelity, and no fatal artifacts. Regenerate once with one targeted correction. Do not silently make endless aesthetic refinements.

## Privacy and memory
Do not auto-save private images as references. Save to registry only when requested or when the user explicitly opts into learning. Use `save_as_reference`, `register_entity`, and `vote_entry` to make preference changes explicit.

## Read when needed
- `references/prompt-contract.md` for templates and structured output.
- `references/model-routing.md` for provider/model decisions.
- `references/quality-gates.md` for scenario checks.
- `references/batch-and-queue.md` for concurrency and retries.
