---
success_required:
  create_image: [status, images, executed_prompt, model_used, modality]
  enhance_prompt: [status, engine, instruction]
  generate_from_template: [status, mode, filled_prompt, slot_values, instruction]
error_types:
  missing_credentials: Set MODAL_BACKEND_URL and redeploy.
  provider_not_registered: Check model-catalog.json and Hermes plugin discovery.
  modality_unsupported: Configure an edit workflow or remove image URLs.
  invalid_parameter: Use values in input.md.
  registry_unavailable: Check HERMES_HOME and storage adapter.
  rate_limited: Retry with exponential backoff.
  generation_failed: Inspect Modal/ComfyUI logs and simplify the workflow.
  entry_not_found: Use list_entities or register_entity.
---

All tool handlers return JSON text and never raise an exception into Hermes.
