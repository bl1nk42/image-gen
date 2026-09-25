---
name: style-learning
description: Learn and improve reusable image styles from liked references, votes, prompts, embeddings, and recent generation outcomes.
---
# Style Learning

When a user asks to learn a style, inspect `semantic_search`, positive/negative votes, and recent registry entries. Use `learn_style` to produce a transparent summary of sample count, positive examples, and learned suffix. Do not silently rewrite a style or treat a single image as a stable preference.

A style may be promoted only when it has multiple positive examples and no unresolved negative pattern. Keep subject details separate from learned style details. When using a learned style in a new prompt, preserve the new subject, composition, and requested text; borrow only lighting, color, material, and mood.
