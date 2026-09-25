# Image Quality Gates

Review generated output against the requested subject, count, pose, composition, aspect ratio, palette, lighting, exact text, reference fidelity, and negative constraints. Mark each as `pass`, `warn`, or `fail` with evidence. A fatal failure is an incorrect subject, changed identity, missing required text, wrong aspect ratio, or an unusable artifact. Regenerate at most once with one targeted correction before reporting the limitation.

For text-bearing images, inspect every character at 100% zoom. For reference edits, compare identity anchors and unchanged regions. For batches, check consistency across the set rather than judging only the best image.
