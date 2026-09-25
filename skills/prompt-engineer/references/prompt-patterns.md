# Prompt Patterns

Use zero-shot for simple stable transformations, few-shot only when examples match the target distribution, and structured JSON when another tool consumes the result. Separate role, task, inputs, constraints, output schema, and failure behavior. Put immutable user facts close to the task and keep optional style guidance separate.

For image prompts, preserve exact names, dates, numbers, and user-provided copy. For optimization, change one instruction at a time and compare against the same test set and seed where possible.
