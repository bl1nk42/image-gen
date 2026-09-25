"""Hermes ImageGenProvider backed by the Modal ComfyUI service."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

try:
    from agent.image_gen_provider import ImageGenProvider, error_response, success_response, DEFAULT_ASPECT_RATIO, normalize_reference_images
except ImportError:  # local smoke-test fallback
    DEFAULT_ASPECT_RATIO = "square"
    class ImageGenProvider: pass
    def success_response(**kwargs): return kwargs
    def error_response(**kwargs): return kwargs
    def normalize_reference_images(items): return items or []

HERE = Path(__file__).resolve().parent
CATALOG = json.loads((HERE / "model-catalog.json").read_text())
from . import tools as memory_tools


def _post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    body = json.dumps(payload).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


class ModalImageGenProvider(ImageGenProvider):
    @property
    def name(self) -> str: return "modal"
    @property
    def display_name(self) -> str: return "Modal + ComfyUI"
    def is_available(self) -> bool: return bool(os.getenv("MODAL_BACKEND_URL"))
    def list_models(self) -> list[dict[str, Any]]: return CATALOG["models"]
    def default_model(self) -> str: return CATALOG["default_model"]
    def get_setup_schema(self) -> dict[str, Any]:
        return {"name": self.display_name, "badge": "self-hosted", "tag": "Qwen/Flux workflows on Modal GPUs", "env_vars": [
            {"key": "MODAL_BACKEND_URL", "prompt": "Deployed Modal generate endpoint"},
            {"key": "MODAL_QUEUE_URL", "prompt": "Optional Modal queue endpoint"},
            {"key": "MODAL_ANALYZE_URL", "prompt": "Optional Modal image-analysis endpoint"},
            {"key": "HF_TOKEN", "prompt": "Optional Hugging Face token", "password": True},
        ]}
    def capabilities(self) -> dict[str, Any]: return {"modalities": ["text", "image-analysis"], "max_reference_images": 0, "queue": True}
    def generate(self, prompt: str, aspect_ratio: str = DEFAULT_ASPECT_RATIO, *, image_url: str | None = None, reference_image_urls: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
        prompt = (prompt or "").strip()
        endpoint = os.getenv("MODAL_BACKEND_URL", "").rstrip("/")
        model = kwargs.get("model") or self.default_model()
        if not prompt: return error_response(error="Prompt is required", error_type="invalid_input", provider=self.name, model=model, prompt=prompt, aspect_ratio=aspect_ratio)
        sources = ([image_url] if image_url else []) + normalize_reference_images(reference_image_urls)
        if sources: return error_response(error="The configured ComfyUI workflow is text-only", error_type="modality_unsupported", provider=self.name, model=model, prompt=prompt, aspect_ratio=aspect_ratio)
        if not endpoint: return error_response(error="MODAL_BACKEND_URL is not configured", error_type="missing_credentials", provider=self.name, model=model, prompt=prompt, aspect_ratio=aspect_ratio)
        try:
            result = _post_json(endpoint, {"prompt": prompt, "negative_prompt": kwargs.get("negative_prompt", ""), "model": model, "aspect_ratio": aspect_ratio, "params": kwargs.get("params", {})})
            if result.get("status") == "error": return error_response(error=result.get("message", "Modal generation failed"), error_type=result.get("error_type", "generation_failed"), provider=self.name, model=model, prompt=prompt, aspect_ratio=aspect_ratio)
            image = result.get("image_url") or result.get("image_b64")
            if result.get("image_b64"):
                from agent.image_gen_provider import save_b64_image
                image = str(save_b64_image(result["image_b64"], prefix="modal", extension="png"))
            return success_response(image=image, model=model, prompt=prompt, aspect_ratio=aspect_ratio, provider=self.name, modality="text", extra={"backend": "modal-comfyui", "width": result.get("width"), "height": result.get("height")})
        except Exception as exc:
            return error_response(error=str(exc), error_type="generation_failed", provider=self.name, model=model, prompt=prompt, aspect_ratio=aspect_ratio)


def register(ctx) -> None:
    ctx.register_image_gen_provider(ModalImageGenProvider())
    descriptions = {
        "get_prompt_catalog": "Return the available prompt vocabularies, styles, presets, and model catalog.",
        "create_image": "Prepare a memory-aware image generation request; use image_generate for the provider call.",
        "edit_image": "Edit an image through an edit-capable ComfyUI workflow.",
        "upscale_image": "Upscale an image through a configured ComfyUI workflow.",
        "enhance_prompt": "Enhance a raw image concept without removing user details.",
        "prepare_prompt_tool": "Normalize inline variables, weights, style suffix, and negative prompt.",
        "generate_from_template": "Fill a character, product, or story image template.",
        "list_styles": "List all available image styles and their prompt suffixes.",
        "upload_asset": "Persist a base64 image asset in the plugin-owned registry.",
        "convert_image_format": "Convert or pass through a base64 image export.",
        "register_entity": "Register an image, prompt, style, template, or category memory entry.",
        "save_as_reference": "Save a liked generated image as a future style reference.",
        "semantic_search": "Search prompt and image memory for related concepts.",
        "upsert_embedding": "Create or update a LanceDB vector memory row from text or a supplied vector.",
        "vector_search": "Run semantic nearest-neighbor search with optional entity type/style filters.",
        "vector_stats": "Inspect vector store path, table, schema, and row count.",
        "export_vectors": "Export vector rows and metadata to JSONL for backup or migration.",
        "import_vectors": "Restore vector rows and metadata from a JSONL export.",
        "delete_embedding": "Delete one vector memory row by entity ID.",
        "list_entities": "List registry entities with optional type filtering.",
        "get_entity": "Retrieve one registry entity by id or keyword.",
        "vote_entry": "Upvote or downvote a memory entry; three downvotes mark it negative.",
        "export_for_generation": "Export a memory entry as a generation reference and recommended prompt.",
        "save_training_pair": "Append a prompt/image training pair to the dataset CSV.",
        "export_dataset_manifest": "Return dataset count and location.",
        "load_model": "Warm or select a Modal model workflow.",
        "analyze_image": "Analyze a base64 image for dimensions and optional semantic caption.",
        "queue_image": "Queue an image request in ComfyUI and return a job ID.",
        "get_job": "Read the status of a queued ComfyUI job.",
        "cancel_job": "Cancel a queued job when the backend exposes cancellation.",
        "cache_stats": "Inspect image and analysis cache freshness without modifying it.",
        "cache_clear": "Clear one cache key or all cache entries with explicit confirmation.",
        "sync_hf_dataset": "Upload the local dataset manifest and assets to a Hugging Face dataset repository.",
        "sync_hf_model": "Upload model or LoRA files to a Hugging Face model repository.",
        "learn_style": "Summarize a style from positive registry examples and votes.",
    }
    for name, handler in memory_tools.HANDLERS.items():
        schema = {"name": name, "description": descriptions.get(name, name.replace("_", " ").title()), "parameters": {"type": "object", "properties": {}, "additionalProperties": True}}
        ctx.register_tool(name=name, toolset="modal-memory", schema=schema, handler=handler)
    ctx.register_command("modal-memory-status", lambda raw: memory_tools.cache_stats({}), description="Show Modal image cache status")
    ctx.register_command("modal-memory-prepare", lambda raw: memory_tools.prepare_prompt_tool({"prompt": raw}), description="Preview normalized image prompt", args_hint="<prompt>")
    def _post_tool_call(tool_name, args, result, **kwargs):
        if tool_name in {"create_image", "analyze_image", "queue_image", "sync_hf_dataset"}:
            memory_tools.record_audit(tool_name, args)
    ctx.register_hook("post_tool_call", _post_tool_call)

__all__ = ["ModalImageGenProvider", "register"]
