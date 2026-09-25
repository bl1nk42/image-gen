# Batch and Queue

Queue independent requests with `queue_image`; record the request signature and returned `job_id`. Poll with `get_job` and never resubmit solely because a job is still running. Retry only transient provider failures, with exponential backoff and a bounded retry count. Dependent edits and continuity scenes must run sequentially and use the actual preceding output.

For each batch, return a manifest containing index, prompt version, seed, model, aspect ratio, job ID, cache state, output path, and quality result. Deduplicate identical signatures before submitting.
