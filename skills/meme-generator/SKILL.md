---
name: meme-generator
description: Create captioned memes from classic templates or a supplied background, with correct text encoding, line limits, preview, and export. Use for memes and social reaction images; do not use for original AI artwork.
---
# Meme Generator

## Route
Use Memegen.link for deterministic classic templates. Use Modal image generation only when the user wants original artwork or a custom scene rather than a classic meme layout.

## Workflow
1. Clarify the joke/take and audience if unclear.
2. Match structure: comparison (Drake/Pooh), hot take (Change My Mind), denial (This Is Fine), dilemma (Daily Struggle), escalation (Galaxy Brain/Vince), misidentification (Pigeon).
3. Keep copy to roughly 3–8 words per line. Match template line count.
4. Encode spaces and punctuation using Memegen rules; use `_` for blank lines.
5. Generate PNG by default, use width 1200 for social cards, download to a descriptive path, and preview.
6. Check legibility, spelling, crop, and whether the punchline matches the template. Regenerate once with shorter copy if needed.

## Do not
Do not overlay text with a script onto an AI-generated blank background when the user asked for an AI visual; do not use the meme route for restoration, photo editing, or non-meme visual work.

Read `references/template-map.md` for template selection and encoding examples.
