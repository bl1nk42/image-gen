---
name: video-generator
description: Plan and execute professional AI video projects including commercials, explainers, short films, social clips, and image-to-video sequences. Use when the user requests video, animation, clips, B-roll, narration, music, or final assembly.
---
# Video Generator

## Phase gate
Gather purpose/audience, narrative arc, duration, aspect ratio, visual style, references, language, recurring elements, dialogue, narration, BGM, and delivery format. Summarize the brief and stop for confirmation before generating. Do not silently assume missing requirements that materially affect the result.

## Blueprint
Define global visual style, recurring characters/objects, voice profiles, BGM source, and clip list. Each clip is 3–10 seconds with one action and one scene. Required fields: narrative purpose, pacing, scene, action/trajectory, detailed transition description (2–4 sentences), duration, camera movement, first-keyframe framing/content, continuity boundary, dialogue, sound effects, BGM cue, narration budget/cue.

## References and execution
Generate reference images before keyframes. Use 16:9 or 9:16, upright. Generate first keyframes, then videos. If a clip reuses a prior frame, wait for the prior render, extract the last decodable frame, verify ratio, then continue sequentially. Queue only independent clips.

## Audio
Keep on-screen dialogue in the video model. Generate narration per span, not one giant track. Preserve video audio, narration, BGM, and SFX by overlaying tracks; never replace one with another. Create an emotional arc table when BGM is separate.

## Delivery gate
Verify duration, aspect ratio, continuity, readable required text, audio presence/levels, and output files. Preserve a manifest with prompts, reference paths, job IDs, and model IDs.
