---
lighting: [natural, studio, dramatic, soft, golden-hour, neon, rim-light, volumetric]
composition: [close-up, medium-shot, wide-shot, portrait, landscape, over-the-shoulder, low-angle, top-down]
camera: [35mm, 50mm, 85mm-portrait, macro, anamorphic, drone]
mood: [tense, hopeful, melancholic, triumphant, serene, mysterious, epic]
entity_types: [image, prompt, style, template, category]
aspect_ratios: [landscape, square, portrait]
weight_range: [0.5, 2.0]
---

# Input contract

Prompt tools accept a string prompt, optional style, negative prompt, aspect ratio, model, seed, and reference URLs. Inline alternatives use `{a|b}` and term weights use `^1.2`; weights are clamped to `[0.5, 2.0]` before generation.
