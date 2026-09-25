---
name: memory-recall
description: Retrieve relevant project decisions, prior prompts, style preferences, debugging notes, and past outputs with source traceability. Use when the user asks what was decided, why a design exists, or wants to reuse a known style/workflow.
---
# Memory Recall

## Retrieval contract
Search narrowly, retrieve multiple candidates, expand only relevant hits, and report source/date plus confidence. Never present a memory as current fact without checking the repository/config when the question concerns current code.

## Workflow
1. Form a query from the user's intent, project name, model/style, and time range if known.
2. Search the memory index or registry with top-k 5.
3. Remove generic or contradictory results.
4. Expand the strongest results and compare decisions, alternatives, and unresolved items.
5. Cross-check current files before recommending a change.
6. Return: key memory, source reference, confidence, and how it affects the current task.

## Image-system memory
Use `semantic_search`, `get_entity`, votes, and `learn_style` for image preferences. Positive examples teach only style/lighting/mood; negative examples become avoided concepts after repeated downvotes. Do not leak image bytes or private prompts into audit logs.

## Failure behavior
If no memory is found, say so. Do not fill the gap with invented history. If memories conflict, show the conflict and prefer the latest verified project state.
