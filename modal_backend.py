"""Modal deployment for the image-generation service.

Deploy:
    modal deploy modal_backend.py

The GPU container runs ComfyUI and exposes a small JSON API. Models are kept in
Modal Volumes so cold starts do not redownload weights. The default workflow is
loaded from /data/workflows/qwen-image-api.json; provide a ComfyUI API-format
workflow with a {prompt} placeholder, or override COMFYUI_WORKFLOW_JSON.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import subprocess
import threading
import time
import urllib.request
import uuid
import urllib.parse
from pathlib import Path
from typing import Any

import modal
from comfy_workflow_adapter import gui_to_api

APP_NAME = os.getenv("MODAL_APP_NAME", "agent-mcp-image-generation")
MODEL_VOLUME_NAME = os.getenv("MODAL_MODEL_VOLUME", "agent-mcp-models")
DATA_VOLUME_NAME = os.getenv("MODAL_DATA_VOLUME", "agent-mcp-image-data")
MODEL_ROOT = "/models"
DATA_ROOT = "/data"
COMFY_ROOT = "/opt/ComfyUI"
COMFY_PORT = 8188

image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04", add_python="3.11")
    .apt_install("git", "libgl1", "libglib2.0-0", "ffmpeg", "wget")
    .run_commands(
        "git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI",
        "pip install --no-cache-dir -r /opt/ComfyUI/requirements.txt",
        "pip install --no-cache-dir fastapi uvicorn pillow requests numpy transformers sentence-transformers huggingface_hub",
    )
    .env({"HF_HOME": f"{MODEL_ROOT}/hf", "TRANSFORMERS_CACHE": f"{MODEL_ROOT}/hf"})
    .add_local_python_source("comfy_workflow_adapter")
    .add_local_file(Path(__file__).parent / "workflows/templates/image_anima_preview.gui.json", "/opt/templates/image_anima_preview.gui.json")
    .add_local_file(Path(__file__).parent / "workflows/templates/image_anima_preview.manifest.json", "/opt/templates/image_anima_preview.manifest.json")
)

app = modal.App(APP_NAME, image=image)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)
data_volume = modal.Volume.from_name(DATA_VOLUME_NAME, create_if_missing=True)


def _aspect_size(aspect_ratio: str) -> tuple[int, int]:
    sizes = {"1:1": (1024, 1024), "16:9": (1344, 768), "9:16": (768, 1344), "4:3": (1152, 896), "3:4": (896, 1152)}
    return sizes.get(aspect_ratio, sizes["1:1"])


def _json_env(name: str) -> dict[str, Any] | None:
    value = os.getenv(name)
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must contain valid JSON: {exc}") from exc


def _cache_key(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@app.cls(
    gpu=os.getenv("MODAL_GPU", "L40S"),
    timeout=60 * 20,
    scaledown_window=10 * 60,
    volumes={MODEL_ROOT: model_volume, DATA_ROOT: data_volume},
)
@modal.concurrent(max_inputs=1)
class Backend:
    """Long-lived ComfyUI worker. One instance owns one GPU and one queue."""

    @modal.enter()
    def enter(self) -> None:
        Path(f"{DATA_ROOT}/outputs").mkdir(parents=True, exist_ok=True)
        Path(f"{DATA_ROOT}/workflows").mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._start_comfyui()
        self._wait_for_comfyui()

    def _start_comfyui(self) -> None:
        cmd = ["python", "main.py", "--listen", "127.0.0.1", "--port", str(COMFY_PORT), "--output-directory", f"{DATA_ROOT}/outputs"]
        self._comfy_process = subprocess.Popen(cmd, cwd=COMFY_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def _wait_for_comfyui(self) -> None:
        deadline = time.time() + 180
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{COMFY_PORT}/system_stats", timeout=2) as response:
                    if response.status == 200:
                        return
            except Exception:
                time.sleep(1)
        raise RuntimeError("ComfyUI did not become ready within 180 seconds")

    def _workflow(self, prompt: str, negative_prompt: str, width: int, height: int, seed: int | None, workflow: dict[str, Any] | None) -> dict[str, Any]:
        wf = workflow or _json_env("COMFYUI_WORKFLOW_JSON")
        if wf is None:
            template_name = os.getenv("COMFYUI_TEMPLATE", "").lower()
            if template_name in {"anima", "anima-preview", "image_anima_preview"}:
                path = Path("/opt/templates/image_anima_preview.gui.json")
            else:
                path = Path(os.getenv("COMFYUI_WORKFLOW_PATH", f"{DATA_ROOT}/workflows/qwen-image-api.json"))
            if not path.exists():
                raise RuntimeError("No ComfyUI workflow found. Set COMFYUI_WORKFLOW_JSON, COMFYUI_WORKFLOW_PATH, or COMFYUI_TEMPLATE=anima.")
            wf = json.loads(path.read_text())
        raw = json.dumps(wf)
        replacements = {"{prompt}": prompt, "{negative_prompt}": negative_prompt, "{width}": str(width), "{height}": str(height), "{seed}": str(seed if seed is not None else int.from_bytes(os.urandom(4), "big"))}
        for old, new in replacements.items():
            raw = raw.replace(old, new)
        return gui_to_api(json.loads(raw), prompt=prompt, negative_prompt=negative_prompt, width=width, height=height, seed=seed)

    def _queue_and_get(self, workflow: dict[str, Any]) -> bytes:
        prompt_id = self._enqueue(workflow)
        return self._wait_for_prompt(prompt_id)

    def _enqueue(self, workflow: dict[str, Any]) -> str:
        client_id = str(uuid.uuid4())
        payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
        request = urllib.request.Request(f"http://127.0.0.1:{COMFY_PORT}/prompt", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read())
        prompt_id = result.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"ComfyUI rejected workflow: {result}")
        return prompt_id

    def _wait_for_prompt(self, prompt_id: str) -> bytes:
        deadline = time.time() + 900
        while time.time() < deadline:
            with urllib.request.urlopen(f"http://127.0.0.1:{COMFY_PORT}/history/{prompt_id}", timeout=10) as response:
                history = json.loads(response.read())
            item = history.get(prompt_id)
            if item and item.get("status", {}).get("completed"):
                for node in item.get("outputs", {}).values():
                    for image in node.get("images", []):
                        params = urllib.parse.urlencode({"filename": image["filename"], "subfolder": image.get("subfolder", ""), "type": image.get("type", "output")})
                        with urllib.request.urlopen(f"http://127.0.0.1:{COMFY_PORT}/view?{params}", timeout=60) as image_response:
                            return image_response.read()
                raise RuntimeError("ComfyUI completed without an image output")
            if item and item.get("status", {}).get("status_str") == "error":
                raise RuntimeError(f"ComfyUI execution failed: {item}")
            time.sleep(1)
        raise TimeoutError("ComfyUI generation timed out")

    @modal.method()
    def generate(self, prompt: str, negative_prompt: str = "", model: str = "qwen-image", aspect_ratio: str = "1:1", image_urls: list[str] | None = None, params: dict[str, Any] | None = None, workflow: dict[str, Any] | None = None) -> dict[str, Any]:
        if image_urls:
            raise ValueError("The default Qwen text-to-image workflow does not accept image URLs; configure an edit workflow explicitly.")
        width, height = _aspect_size(aspect_ratio)
        params = params or {}
        cache_payload = {"prompt": prompt, "negative_prompt": negative_prompt, "model": model, "aspect_ratio": aspect_ratio, "params": params}
        cache_file = Path(DATA_ROOT) / "cache" / f"{_cache_key(cache_payload)}.json"
        if cache_file.exists() and time.time() - cache_file.stat().st_mtime <= int(os.getenv("IMAGE_CACHE_TTL_SECONDS", "86400")):
            return {**json.loads(cache_file.read_text()), "from_cache": True}
        wf = self._workflow(prompt, negative_prompt, int(params.get("width", width)), int(params.get("height", height)), params.get("seed"), workflow)
        with self._lock:
            image_bytes = self._queue_and_get(wf)
        digest = hashlib.sha256(image_bytes).hexdigest()[:16]
        path = Path(DATA_ROOT) / "outputs" / f"{digest}.png"
        path.write_bytes(image_bytes)
        data_url = "data:image/png;base64," + base64.b64encode(image_bytes).decode()
        result = {"image_b64": base64.b64encode(image_bytes).decode(), "image_url": data_url, "width": width, "height": height, "model": model, "path": str(path), "from_cache": False}
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(result))
        return result

    @modal.method()
    def enqueue(self, prompt: str, negative_prompt: str = "", model: str = "qwen-image", aspect_ratio: str = "1:1", params: dict[str, Any] | None = None, workflow: dict[str, Any] | None = None) -> dict[str, Any]:
        width, height = _aspect_size(aspect_ratio)
        wf = self._workflow(prompt, negative_prompt, int((params or {}).get("width", width)), int((params or {}).get("height", height)), (params or {}).get("seed"), workflow)
        with self._lock:
            prompt_id = self._enqueue(wf)
        return {"job_id": prompt_id, "status": "queued", "model": model, "width": width, "height": height}

    @modal.method()
    def job_status(self, job_id: str) -> dict[str, Any]:
        with urllib.request.urlopen(f"http://127.0.0.1:{COMFY_PORT}/history/{urllib.parse.quote(job_id)}", timeout=15) as response:
            history = json.loads(response.read())
        item = history.get(job_id)
        if not item: return {"job_id": job_id, "status": "queued"}
        status = item.get("status", {})
        return {"job_id": job_id, "status": "completed" if status.get("completed") else status.get("status_str", "running"), "outputs": item.get("outputs", {})}

    @modal.method()
    def analyze_image(self, image_b64: str, task: str = "caption") -> dict[str, Any]:
        from PIL import Image
        image = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
        result: dict[str, Any] = {"task": task, "width": image.width, "height": image.height, "format": image.format, "mode": image.mode, "caption": None}
        if task in {"caption", "all"}:
            try:
                from transformers import BlipForConditionalGeneration, BlipProcessor
                import torch
                if not hasattr(self, "caption_model"):
                    name = os.getenv("IMAGE_CAPTION_MODEL", "Salesforce/blip-image-captioning-base")
                    self.caption_processor = BlipProcessor.from_pretrained(name, cache_dir=f"{MODEL_ROOT}/hf")
                    self.caption_model = BlipForConditionalGeneration.from_pretrained(name, cache_dir=f"{MODEL_ROOT}/hf").to("cuda")
                inputs = self.caption_processor(images=image, return_tensors="pt").to("cuda")
                with torch.inference_mode():
                    result["caption"] = self.caption_processor.decode(self.caption_model.generate(**inputs, max_new_tokens=40)[0], skip_special_tokens=True)
            except Exception as exc:
                result["caption_error"] = str(exc)
        return result

    @modal.method()
    def embed_text(self, text: str) -> list[float]:
        from sentence_transformers import SentenceTransformer
        if not hasattr(self, "embedder"):
            self.embedder = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"), cache_folder=f"{MODEL_ROOT}/hf")
        return self.embedder.encode(text, normalize_embeddings=True).astype("float32").tolist()

    @modal.method()
    def embed_image(self, image_b64: str) -> list[float]:
        from PIL import Image
        from transformers import CLIPModel, CLIPProcessor
        if not hasattr(self, "clip_model"):
            name = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained(name, cache_dir=f"{MODEL_ROOT}/hf")
            self.clip_model = CLIPModel.from_pretrained(name, cache_dir=f"{MODEL_ROOT}/hf").to("cuda")
        import torch
        image = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
        inputs = self.clip_processor(images=image, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            vector = self.clip_model.get_image_features(**inputs)
            vector = vector / vector.norm(dim=-1, keepdim=True)
        return vector[0].float().cpu().tolist()

    @modal.method()
    def warmup(self, model_id: str = "qwen-image", lora_path: str | None = None) -> dict[str, Any]:
        return {"status": "success", "model_id": model_id, "message": "ComfyUI worker is warm; model workflow will be loaded on first queue", "lora_path": lora_path}


@app.function(timeout=60 * 20)
@modal.fastapi_endpoint(method="POST", docs=True)
def generate_api(payload: dict[str, Any]) -> dict[str, Any]:
    """Public JSON endpoint consumed by the Hermes plugin and FastAPI adapter."""
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return {"status": "error", "error_type": "invalid_parameter", "message": "prompt is required"}
    result = Backend().generate.remote(prompt=prompt, negative_prompt=str(payload.get("negative_prompt", "")), model=str(payload.get("model", "qwen-image")), aspect_ratio=str(payload.get("aspect_ratio", "1:1")), image_urls=payload.get("image_urls"), params=payload.get("params"), workflow=payload.get("workflow"))
    return {"status": "success", **result}


@app.function(timeout=60 * 20)
@modal.fastapi_endpoint(method="POST", docs=True)
def queue_api(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt: return {"status": "error", "error_type": "invalid_parameter", "message": "prompt is required"}
    result = Backend().enqueue.remote(prompt=prompt, negative_prompt=str(payload.get("negative_prompt", "")), model=str(payload.get("model", "qwen-image")), aspect_ratio=str(payload.get("aspect_ratio", "1:1")), params=payload.get("params"), workflow=payload.get("workflow"))
    return {"status": "success", **result}


@app.function(timeout=60)
@modal.fastapi_endpoint(method="POST", docs=True)
def analyze_api(payload: dict[str, Any]) -> dict[str, Any]:
    raw = str(payload.get("image_b64", ""))
    if not raw: return {"status": "error", "error_type": "invalid_parameter", "message": "image_b64 is required"}
    return {"status": "success", **Backend().analyze_image.remote(raw, str(payload.get("task", "caption")))}


@app.function(timeout=60 * 10)
@modal.fastapi_endpoint(method="POST", docs=True)
def embed_text_api(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text", "")).strip()
    if not text: return {"status": "error", "error_type": "invalid_parameter", "message": "text is required"}
    return {"status": "success", "embedding": Backend().embed_text.remote(text), "model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")}


@app.function(timeout=60 * 20)
@modal.fastapi_endpoint(method="POST", docs=True)
def embed_image_api(payload: dict[str, Any]) -> dict[str, Any]:
    raw = str(payload.get("image_b64", ""))
    if not raw: return {"status": "error", "error_type": "invalid_parameter", "message": "image_b64 is required"}
    return {"status": "success", "embedding": Backend().embed_image.remote(raw), "model": os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")}


@app.function(timeout=60)
@modal.fastapi_endpoint(method="POST", docs=True)
def job_status_api(payload: dict[str, Any]) -> dict[str, Any]:
    job_id = str(payload.get("job_id", "")).strip()
    if not job_id: return {"status": "error", "error_type": "invalid_parameter", "message": "job_id is required"}
    return {"status": "success", **Backend().job_status.remote(job_id)}


@app.function()
@modal.fastapi_endpoint(method="GET")
def model_catalog() -> dict[str, Any]:
    path = Path(os.getenv("MODEL_CATALOG_PATH", f"{DATA_ROOT}/model-catalog.json"))
    if path.exists(): return json.loads(path.read_text())
    return {"version": 1, "default_model": "qwen-image", "providers": {"modal": {"models": [{"id": "qwen-image", "default": True}]}}}


@app.function(image=image, timeout=60 * 60 * 4, volumes={MODEL_ROOT: model_volume})
def prepare_anima_models() -> dict[str, Any]:
    """Explicitly download the public Anima model files into the Modal Volume."""
    from huggingface_hub import hf_hub_download
    repo = "circlestone-labs/Anima"
    files = {
        "text_encoders": "split_files/text_encoders/qwen_3_06b_base.safetensors",
        "vae": "split_files/vae/qwen_image_vae.safetensors",
        "diffusion_models": "split_files/diffusion_models/anima-preview3-base.safetensors",
    }
    paths = {}
    for folder, filename in files.items():
        target = Path(MODEL_ROOT) / folder
        target.mkdir(parents=True, exist_ok=True)
        downloaded = hf_hub_download(repo_id=repo, filename=filename, cache_dir=f"{MODEL_ROOT}/hf")
        destination = target / Path(filename).name
        import shutil
        shutil.copy2(downloaded, destination)
        paths[folder] = str(destination)
    return {"status": "success", "repo": repo, "files": paths, "model_volume": MODEL_VOLUME_NAME}


@app.function()
@modal.fastapi_endpoint(method="GET")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.local_entrypoint()
def main(prompt: str = "a cinematic mountain sunset", aspect_ratio: str = "16:9") -> None:
    result = generate_api.remote({"prompt": prompt, "aspect_ratio": aspect_ratio})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print(f"Deploy with: modal deploy {Path(__file__).name}")
    print(f"App: {APP_NAME}; model volume: {MODEL_VOLUME_NAME}; data volume: {DATA_VOLUME_NAME}")
