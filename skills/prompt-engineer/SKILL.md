---
name: prompt-engineer
description: Design, refactor, evaluate, and version prompts for image generation, image analysis, style learning, and structured agent tools. Use when outputs are inconsistent, prompts need optimization, or a new provider/model is introduced.
---
# Prompt Engineer

## Contract-first method
Define task, input variables, output shape, success metric, cost/latency budget, safety constraints, and known failure modes before writing the prompt. Keep user facts separate from optional enhancement. Use structured output when a downstream tool consumes the result.

## Image prompt method
Use five blocks: purpose/medium; subject facts; composition/camera; lighting/material/mood; exact text and exclusions. Put learned style after subject facts. Use deterministic inline choices and clamp weights to `[0.5, 2.0]`. Never add unrelated subject details just to make a prompt sound vivid.

## Evaluation
Create a small test set with normal, empty, multilingual, long, conflicting, text-bearing, reference-image, and adversarial inputs. Score prompt preservation, schema validity, model adherence, and consistency. If the baseline is below 80%, identify one failure pattern and change one prompt element at a time. Record version, model, parameters, result, and human/automatic score with `register_entity` or dataset metadata.

## Deployment
Do not replace a production prompt without comparing old/new outputs. Keep rollback text. Report known limitations and provider-specific differences in `model-catalog.json` metadata.

Read `references/prompt-patterns.md`, `references/evaluation-rubric.md`, and `references/structured-output.md` when designing a new workflow.
