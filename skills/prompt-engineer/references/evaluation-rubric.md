# Prompt Evaluation Rubric

Score each case 0–2 for: fact preservation, composition adherence, style isolation, text accuracy, negative constraint, schema validity, and reproducibility. A case passes at 10/14; a suite passes at 80% of cases. Include empty prompt, Thai/English mixed prompt, long prompt, `{a|b}`, invalid weight, exact dates/numbers, reference image, and adversarial instruction injection.

Record:

```json
{"prompt_version":"v1","model":"qwen-image","seed":42,"case":"thai-text","scores":{"facts":2,"composition":1,"style":2,"text":2,"negative":2,"schema":2,"repeat":2},"failure":"none"}
```
