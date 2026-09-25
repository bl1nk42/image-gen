---
name: nothing-design
description: Apply the Nothing-inspired monochrome industrial design system to interfaces, dashboards, image prompts, and generated visual references. Use only when the user explicitly requests Nothing style/design or invokes this skill.
---
# Nothing Design

## Before design
Declare the font plan: Space Grotesk for display/body and Space Mono for labels/data; use Doto only for one hero moment if available. State dark or light mode. If Google Fonts are unavailable, provide a local fallback and do not pretend it matches exactly.

## Hierarchy
Every screen has three layers: one primary focal point, supporting secondary context, and tertiary metadata. Use scale and spacing rather than decorative cards. Use at most two families, three sizes, and two weights per screen. Make asymmetry intentional and reserve one visual surprise.

## Tokens
Dark: OLED black canvas, white display text, 90% primary, 60% secondary, 40% disabled. Light: warm off-white canvas with the same hierarchy. Red is an interrupt, not a default accent. Avoid gradients, blur, shadows, noisy icons, excessive rounded cards, toast popups, and decorative illustrations.

## For generated images
Use the visual direction as prompt constraints: monochrome palette, exposed grid, precise typography, technical labels, industrial materials, high negative space, one red status accent only when semantically needed. For exact text or pixel-perfect UI, create editable layout/source rather than trusting generated typography.

## Review
Check hierarchy at a glance, spacing relationships, color role limits, font loading, contrast, responsive behavior, and whether every element earns its place. Read `references/tokens.md` and `references/components.md` before implementing a concrete screen.
