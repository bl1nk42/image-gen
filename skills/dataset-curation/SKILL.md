---
name: dataset-curation
description: Curate generated images into a clean training dataset, validate metadata, remove duplicates, and sync manifests/assets to Hugging Face.
---
# Dataset Curation

Use this skill when the user asks to collect, clean, label, export, or publish image-generation training data. Never publish automatically. First inspect the manifest with `export_dataset_manifest`, validate that each row has an executed prompt, raw concept, image path, model, style, tags, and quality score, then check duplicates and negative votes.

Use `save_training_pair` for a local append-only record. Use `sync_hf_dataset` only after the user explicitly asks to sync or publish and the repository/token are configured. Prefer a dataset repository for CSV/JSONL and assets; use a model repository for model weights or LoRA files. Report repository URL and commit result.

Recommended lifecycle: collect -> validate -> deduplicate -> review negatives -> export manifest -> sync to Hugging Face.
