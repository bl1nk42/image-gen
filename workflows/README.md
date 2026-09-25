# ComfyUI workflow contract

ComfyUI exposes two different workflow representations. The canvas/editor export contains `nodes`, `links`, and `definitions`; the `/prompt` endpoint accepts an API-format map whose values contain `class_type` and `inputs`. They are not interchangeable.

The attached user workflow is preserved as [`templates/image_anima_preview.gui.json`](templates/image_anima_preview.gui.json). It contains the `Text to Image (Anima)` subgraph and references:

```text
models/diffusion_models/anima-preview3-base.safetensors
models/text_encoders/qwen_3_06b_base.safetensors
models/vae/qwen_image_vae.safetensors
```

`comfy_workflow_adapter.py` converts this exact Anima canvas export into the API node map before the Modal worker calls ComfyUI `/prompt`. The adapter preserves the CLIP loader, VAE loader, UNET loader, positive/negative text encoders, KSampler, VAE decode, and SaveImage nodes while replacing prompt, negative prompt, width, height, and seed at request time.

## Use the supplied template

Set `COMFYUI_TEMPLATE=anima`. The Modal image includes the template at `/opt/templates/image_anima_preview.gui.json`; the worker gives this template precedence over the generic Qwen path. Run `modal run modal_backend.py::prepare_anima_models` once after Modal authentication to populate the model Volume.

## Use another ComfyUI workflow

In ComfyUI use **Queue Prompt → Save (API Format)** and place the resulting JSON at `/data/workflows/qwen-image-api.json`, or set `COMFYUI_WORKFLOW_PATH`. API-format JSON may contain `{prompt}`, `{negative_prompt}`, `{width}`, `{height}`, and `{seed}` placeholders. Custom nodes and model filenames must exist in the same Modal image/Volume configuration as the exported workflow.
