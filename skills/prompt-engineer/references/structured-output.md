# Structured Output

Define required fields, types, enums, and nullable behavior before implementation. Require the model to return only the schema when downstream parsing is strict. Validate locally and return a remediation error rather than silently coercing missing fields. Include `status`, `error_type`, `message`, and `remediation` in failure responses.

For image jobs, use `status`, `images`, `executed_prompt`, `model_used`, `modality`, `from_cache`, `job_id`, and `quality` as the stable contract.
