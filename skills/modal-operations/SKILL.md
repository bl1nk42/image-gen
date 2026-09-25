---
name: modal-operations
description: Deploy, inspect, warm, cache, and troubleshoot the Modal + ComfyUI image backend and Hugging Face storage.
---
# Modal Operations

Use `install.py`, `modal deploy modal_backend.py`, and the commands in the repository guide. Check `health` before generation. Use `cache_stats` and `cache_clear` for cache operations; clearing all cache requires explicit confirmation. Use `load_model` to warm a workflow. Never expose HF tokens or Modal secrets in output.

When a job fails, inspect the backend health, ComfyUI workflow path, model Volume contents, and queue status in that order. Do not ask the user to reinstall if the failure is a missing workflow or credential; report the exact remediation.
