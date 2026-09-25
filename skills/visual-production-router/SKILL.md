---
name: visual-production-router
description: Route visual requests to image generation, restoration, Nothing design, memes, character stories, video production, prompt engineering, memory, or the exact Modal tools. Use when a request spans multiple visual modalities or the right workflow is unclear.
---
# Visual Production Router

Classify the user's intended deliverable before calling a tool. Use `image-generation` for new/edit images, `photo-restoration` for preservation-first recovery, `nothing-design` only for explicit Nothing requests, `meme-generator` for classic captioned templates, `character-story-video` for identity-consistent sequences, and `video-generator` for commercials, explainers, films, or general video. Use `prompt-engineer` when reliability or evaluation is the problem and `memory-recall` when prior decisions or preferences matter.

For mixed requests, compose skills in this order: retrieve verified memory; write the creative/technical brief; select models and references; generate or queue assets; analyze and quality-check; register only with consent; assemble and deliver a manifest. Keep deterministic diagrams/charts outside generative image routes.

Before execution, state the selected route and the one material assumption. After execution, return source assets, prompts, model IDs, cache/job status, quality result, and next reversible action.
