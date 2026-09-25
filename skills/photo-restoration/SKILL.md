---
name: photo-restoration
description: Restore blurry, damaged, faded, or vintage photos while preserving identity, pose, composition, clothing, and historical character. Use for restoration, deblur, denoise, color correction, facial recovery, and high-resolution enhancement.
---
# Photo Restoration

## Non-negotiable objective
Improve legibility and fidelity without inventing a new person or changing the original event. Treat identity, expression, pose, clothing, framing, background, and era as preservation constraints.

## Workflow
1. Inspect the source with `analyze_image`: dimensions, crop, blur, damage, faces, text, and color condition.
2. Classify the request: conservative restoration, colorization, face recovery, scratch/damage repair, or upscale. Ask only if the requested level of invention is unclear.
3. Create a restoration brief that lists what may change and what must not change.
4. Use image edit/variation with a prompt that says “change only” the listed defects. Never use a generic beauty prompt.
5. Cache by source hash plus restoration profile. Preserve the original and output as separate assets.
6. Run the preservation gate: identity, count of people, pose, clothing, composition, background, and text must remain consistent.

## Prompt template
“Restore the provided photograph. Improve [specific defects]. Preserve exactly: identity and facial proportions, expression, pose, body proportions, clothing, objects, background, camera angle, framing, historical era, and all readable text. Reconstruct only missing pixels required by the defects. Do not beautify, modernize, change age, add objects, remove people, or alter composition. Output a natural high-resolution photograph consistent with the original.”

## Escalation
If the source is too damaged to preserve identity, report uncertainty and produce a conservative result rather than confident invention. If the user requests a creative reinterpretation, route to image-generation instead and label it as reinterpretation.

## Read when needed
- `references/restoration-profiles.md` for conservative, portrait, document, colorization, and damage-repair profiles.
- `references/preservation-checklist.md` for pass/fail review.
