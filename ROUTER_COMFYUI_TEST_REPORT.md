# Router and ComfyUI Template Test Report

## Scope

The supplied `image_anima_preview.json` was tested with the Visual Production Router, image-generation workflow, video-generator workflow, and Modal/ComfyUI adapter. The test used the actual attachment rather than a synthetic sample.

## Findings

The attachment is a ComfyUI **GUI canvas export**. It contains three top-level nodes, one `Text to Image (Anima)` subgraph with nine nodes, and nineteen subgraph links. It is not an API-format workflow because it does not map node IDs to `class_type` and `inputs`. Sending it directly to ComfyUI `/prompt` would not match the API contract.

The project now preserves the original GUI export and converts it through `comfy_workflow_adapter.py` into a nine-node API workflow. The adapter maps the CLIP loader, VAE loader, UNET loader, EmptyLatentImage, positive and negative CLIPTextEncode nodes, KSampler, VAEDecode, and SaveImage. It replaces prompt, negative prompt, width, height, and seed without changing the model filenames.

## Router dry-run

For a still-image request, the route is `visual-production-router → image-generation → Modal + ComfyUI`. The video-generator skill is intentionally not invoked because that would be an incorrect modality route.

For a character-video request, the route is `visual-production-router → image-generation` for the character anchor and reference images, followed by `video-generator` for the clip blueprint and image-to-video stage. The test verifies the required gates: brief confirmation, reference images before keyframes, 16:9 or 9:16 output, and sequential execution for dependent scenes.

## Modal status

The code now installs ComfyUI from the official repository inside the Modal GPU image. It explicitly mounts the supplied GUI template with `modal.Image.add_local_file`, explicitly adds the local adapter module with `add_local_python_source`, and includes a `prepare_anima_models` Modal function that downloads the three public Anima files into the model Volume.

A real Modal deployment was not performed in this session. `modal --version` returned `0.77.0`, but `modal app list` stopped with `Token missing`. Therefore there is no truthful claim that ComfyUI is currently running on the user's Modal account. Deployment requires Modal authentication, followed by `modal deploy modal_backend.py` and `modal run modal_backend.py::prepare_anima_models`.

## Validation results

```text
ROUTER_COMFY_TEMPLATE_DRY_RUN_OK
ALL SMOKE TESTS PASSED
SKILL PACK VALID
MODAL_IMPORT_OK_FINAL
```
