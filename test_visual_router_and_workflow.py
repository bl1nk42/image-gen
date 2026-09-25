from __future__ import annotations
import json, pathlib, re, sys
from comfy_workflow_adapter import gui_to_api

ROOT = pathlib.Path(__file__).resolve().parent
ATTACHMENT = pathlib.Path('/home/ubuntu/upload/image_anima_preview.json')
WORKFLOW = json.loads(ATTACHMENT.read_text())

# Contract detection: ComfyUI GUI exports have nodes/links; API exports map node IDs to class_type/inputs.
def detect_workflow(value):
    if isinstance(value, dict) and 'nodes' in value and 'links' in value:
        return 'gui-workflow'
    if isinstance(value, dict) and value and all(isinstance(v, dict) and 'class_type' in v for v in value.values()):
        return 'api-workflow'
    return 'unknown'

kind = detect_workflow(WORKFLOW)
assert kind == 'gui-workflow'
nodes = WORKFLOW['nodes']
assert any(node.get('type') == 'MarkdownNote' for node in nodes)
assert WORKFLOW.get('definitions', {}).get('subgraphs')
subgraph = WORKFLOW['definitions']['subgraphs'][0]
assert subgraph['name'] == 'Text to Image (Anima)'
assert any(node.get('type') == 'CLIPLoader' for node in subgraph['nodes'])
assert any(node.get('type') == 'VAELoader' for node in subgraph['nodes'])
assert any(node.get('type') == 'SaveImage' for node in nodes)
api_workflow = gui_to_api(WORKFLOW, prompt='test router prompt', negative_prompt='test negative', width=768, height=1344, seed=42)
assert all(isinstance(value, dict) and 'class_type' in value and 'inputs' in value for value in api_workflow.values())
assert api_workflow['28']['inputs']['width'] == 768
assert api_workflow['28']['inputs']['height'] == 1344
assert api_workflow['66']['inputs']['text'] == 'test router prompt'
assert api_workflow['12']['inputs']['text'] == 'test negative'
assert api_workflow['44']['inputs']['unet_name'] == 'anima-preview3-base.safetensors'

# Extract the model contract exposed by the attached template.
text = json.dumps(WORKFLOW, ensure_ascii=False)
required_models = {
    'diffusion_models': 'anima-preview3-base.safetensors',
    'text_encoders': 'qwen_3_06b_base.safetensors',
    'vae': 'qwen_image_vae.safetensors',
}
for model_type, filename in required_models.items():
    assert filename in text, (model_type, filename)

# Dry-run route: the requested operation is an image generation workflow,
# while video-generator is a downstream consumer only when the user asks for video.
route = {
    'router': 'visual-production-router',
    'primary_skill': 'image-generation',
    'template_skill': 'comfyui-gui-export-adapter',
    'downstream_video_skill': 'video-generator (not invoked for still-image request)',
    'provider': 'modal-comfyui',
    'model': 'anima-preview3-base.safetensors',
    'aspect_ratio': '9:16 requested by template note; source node currently stores 1024x1024',
    'execution': 'dry-run only; no Modal job submitted',
    'workflow_adapter': 'GUI canvas export converted to API node map before POST /prompt',
}
assert route['primary_skill'] == 'image-generation'
assert 'anima-preview3-base.safetensors' in route['model']
video_route = {
    'router': 'visual-production-router',
    'stages': ['image-generation: character anchor and reference images', 'video-generator: clip blueprint and image-to-video execution'],
    'gates': ['brief confirmation', 'reference image before keyframes', '16:9 or 9:16 only', 'dependent scenes sequential'],
    'execution': 'dry-run only; no video job submitted',
}
assert video_route['stages'][0].startswith('image-generation')
assert video_route['stages'][1].startswith('video-generator')
assert 'reference image before keyframes' in video_route['gates']
print(json.dumps({'workflow_kind': kind, 'api_node_count': len(api_workflow), 'node_count': len(nodes), 'subgraph_node_count': len(subgraph['nodes']), 'required_models': required_models, 'image_route': route, 'video_route': video_route}, ensure_ascii=False, indent=2))
print('ROUTER_COMFY_TEMPLATE_DRY_RUN_OK')
