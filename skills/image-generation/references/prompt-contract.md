# Prompt Contract

## Canonical prompt
```text
Create [asset] for [purpose/medium].
Subject: [immutable subject facts].
Composition: [orientation, framing, focal point, safe area, camera].
Style and light: [requested or learned style only].
Text to render: [exact text, language, hierarchy] OR no text.
Constraints: [aspect ratio, transparency, reference fidelity].
Avoid: [negative concepts].
```

## Result contract
Return `status`, `image(s)`, `model_used`, `provider`, `modality`, `executed_prompt`, `negative_prompt`, `aspect_ratio`, `from_cache`, `job_id`, and `registry_status`. On failure return `error_type`, `message`, and `remediation`.

## Variable policy
Resolve `{a|b}` deterministically using seed. Clamp `^weight` to `[0.5, 2.0]`. Do not use inline alternatives for legal text, names, prices, dates, or required copy.
