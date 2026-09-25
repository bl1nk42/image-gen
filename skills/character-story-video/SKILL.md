---
name: character-story-video
description: Plan and produce a multi-part animated character story with stable identity, sequential scenes, reference images, image-to-video clips, audio planning, and continuity checks. Use for character stories, sequels, animated narratives, or multi-scene image/video sequences.
---
# Character Story Video

## Inputs
Require character description and story premise. Capture reference image if available, target audience, language, duration, aspect ratio (16:9 or 9:16), visual style, dialogue/narration, and BGM decision. Stop for confirmation after the brief and before execution.

## Phases
1. **Character anchor:** generate or inspect one primary character reference. Record identity anchors: face, hair, outfit, silhouette, palette, age, proportions, and expression range. Obtain approval before scenes.
2. **Story beats:** create beginning/middle/end or a user-specified beat list. Each scene has one action, one location, one camera movement, and a continuity note.
3. **Reference set:** generate only the angles/shots actually needed, always deriving secondary references from the primary anchor.
4. **Scene images:** generate sequentially when continuity depends on prior output; otherwise queue independent scenes. Register each asset and prompt.
5. **Animation:** create 3–10 second clips. Every transition description must include appearance, movement trajectory, state changes, and what remains present throughout. Preserve audio tracks when mixing.
6. **Assembly:** concatenate only after clip checks; keep source assets, prompts, job IDs, and a manifest.

## Hard checks
Never use 1:1 for video keyframes. Do not use TTS for on-screen dialogue. Do not skip reference images. Do not generate a dependent scene in parallel. If a scene has no traversable physical path, split it.

Use the queue for independent clips and `get_job` for polling. Use the video production skill for music, narration, and final audio mix.
