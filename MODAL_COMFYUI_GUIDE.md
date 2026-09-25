# Modal + ComfyUI + Hermes/Claude Image System

This repository provides a GPU image backend plus two integration surfaces: a Hermes image provider/plugin and a portable Claude Code plugin. The backend runs ComfyUI on Modal, stores model/output data in Modal Volumes, caches deterministic image requests for 24 hours by default, exposes queue/status endpoints, and can caption images with BLIP. The plugin stores registry metadata and dataset manifests locally, then optionally syncs to Hugging Face Hub.

## Deploy backend

```bash
python -m pip install -r requirements-modal.txt
modal setup
modal volume create agent-mcp-models --version=2
modal volume create agent-mcp-image-data --version=2
modal deploy modal_backend.py
```

The Modal image installs ComfyUI from the official GitHub repository during image build. The user-supplied Anima canvas export is bundled at `/opt/templates/image_anima_preview.gui.json`; it is not sent directly to `/prompt` because ComfyUI's `/prompt` endpoint accepts API-format node maps. `comfy_workflow_adapter.py` converts this exact GUI export, including its `Text to Image (Anima)` subgraph, to an API node map before queueing.

The supplied template requires these files in the mounted model Volume:

```text
/models/diffusion_models/anima-preview3-base.safetensors
/models/text_encoders/qwen_3_06b_base.safetensors
/models/vae/qwen_image_vae.safetensors
```

After authentication, prepare them with the included Modal function:

```bash
modal run modal_backend.py::prepare_anima_models
```

For the supplied template set `COMFYUI_TEMPLATE=anima`. For other ComfyUI templates, export **Queue Prompt → Save (API Format)** and put the JSON at `/data/workflows/qwen-image-api.json` or set `COMFYUI_WORKFLOW_PATH`. API-format templates may contain `{prompt}`, `{negative_prompt}`, `{width}`, `{height}`, and `{seed}` placeholders. The original GUI export and manifest are retained under `workflows/templates/`.

The deployment exposes `generate_api`, `queue_api`, `job_status_api`, `analyze_api`, `health`, and `model_catalog`. Modal prints their URLs after deployment. Set:

```env
MODAL_BACKEND_URL=https://...generate-api.modal.run
MODAL_QUEUE_URL=https://...queue-api.modal.run
MODAL_JOB_STATUS_URL=https://...job-status-api.modal.run
MODAL_ANALYZE_URL=https://...analyze-api.modal.run
IMAGE_CACHE_TTL_SECONDS=86400
```

## Install integrations with one command

Linux/macOS:

```bash
./install.sh --claude
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1 -Claude
```

Or run the portable installer directly:

```bash
python install.py --claude --home ~/.hermes
```

The installer copies the Hermes provider and the Claude plugin. It does not copy secrets or publish data.

## Hugging Face model and dataset storage

Use a **model repository** for model weights/LoRA files and a **dataset repository** for `train.csv`, JSONL registry exports, image assets, and manifests:

```env
HF_TOKEN=hf_...
HF_MODEL_REPO=org/image-models
HF_DATASET_REPO=org/image-generation-dataset
```

The `sync_hf_model` and `sync_hf_dataset` operations call `huggingface_hub.HfApi`, create the repository if needed, and upload the selected local folder. Publishing is never automatic; use the dataset curation skill/command and confirm before syncing.

## Cache and queue behavior

`create_image` hashes prompt, negative prompt, model, aspect ratio, and parameters. A fresh matching result returns immediately with `from_cache: true`. `cache_stats` is read-only. Clearing one key is reversible; clearing all entries requires `confirm=true`.

`queue_image` submits an asynchronous ComfyUI job and returns a `job_id`. `get_job` queries the status endpoint when configured. The queue is implemented using ComfyUI's own prompt queue and Modal autoscaling; a separate polling daemon is not required.

## Component placement

- **Provider:** image generation dispatch and Hermes model picker.
- **Tools:** binary image analysis, API calls, cache, queue, registry, and HF upload.
- **Skills:** image generation, dataset curation, style learning, and Modal operations.
- **Commands:** prompt preview, image status, and dataset sync.
- **Agent:** style curator for multi-step evidence-based style updates.
- **Hooks:** metadata-only lifecycle audit after image, queue, vision, and sync operations.

This follows Hermes guidance: use a skill for instructions plus existing tools; use a tool for API keys, custom processing, binary data, streaming, or real-time state.
