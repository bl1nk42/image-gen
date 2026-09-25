---
description: Validate the local image dataset manifest and sync it to Hugging Face after confirmation
argument-hint: [repo_id]
---
Run `export_dataset_manifest`, summarize missing fields and row count, and ask for confirmation before calling `sync_hf_dataset`. Never publish without explicit confirmation.
