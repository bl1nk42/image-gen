"""Adapters for ComfyUI workflow exports.

ComfyUI's canvas JSON is not the payload accepted by POST /prompt. This module
keeps the original canvas export as the source of truth and converts the
provided Anima subgraph into the API node map that ComfyUI expects.
"""
from __future__ import annotations
import copy
from typing import Any


def is_api_workflow(value: dict[str, Any]) -> bool:
    return bool(value) and all(isinstance(v, dict) and "class_type" in v and "inputs" in v for v in value.values())


def _link_map(subgraph: dict[str, Any]) -> dict[int, tuple[int, int]]:
    return {int(link["id"]): (int(link["origin_id"]), int(link["origin_slot"])) for link in subgraph.get("links", [])}


def _ref(link_id: int | None, links: dict[int, tuple[int, int]]) -> list[Any] | None:
    if link_id is None or link_id not in links:
        return None
    source, slot = links[link_id]
    if source < 0:
        return None
    return [str(source), slot]


def _input(node: dict[str, Any], name: str, links: dict[int, tuple[int, int]]) -> list[Any] | None:
    for item in node.get("inputs", []):
        if item.get("name") == name:
            return _ref(item.get("link"), links)
    return None


def _widget(node: dict[str, Any], name: str, default: Any = None) -> Any:
    named = node.get("widgets_values_named") or {}
    if name in named:
        return copy.deepcopy(named[name])
    return default


def gui_to_api(gui: dict[str, Any], prompt: str | None = None, negative_prompt: str | None = None, width: int | None = None, height: int | None = None, seed: int | None = None) -> dict[str, Any]:
    """Convert the supplied Anima canvas export to a ComfyUI API node map."""
    if is_api_workflow(gui):
        return copy.deepcopy(gui)
    if not isinstance(gui, dict) or "definitions" not in gui or "nodes" not in gui:
        raise ValueError("Workflow is neither ComfyUI API format nor a GUI canvas export")
    subgraphs = gui.get("definitions", {}).get("subgraphs", [])
    subgraph = next((x for x in subgraphs if x.get("name") == "Text to Image (Anima)"), None)
    if subgraph is None:
        raise ValueError("GUI export does not contain the expected 'Text to Image (Anima)' subgraph")
    nodes = {int(n["id"]): n for n in subgraph.get("nodes", []) if int(n["id"]) > 0}
    links = _link_map(subgraph)
    by_type = {node.get("type"): node for node in nodes.values()}
    required = ["CLIPLoader", "VAELoader", "UNETLoader", "EmptyLatentImage", "CLIPTextEncode", "KSampler", "VAEDecode"]
    missing = [name for name in required if name not in by_type]
    if missing:
        raise ValueError(f"Anima GUI export is missing required nodes: {', '.join(missing)}")
    clip = by_type["CLIPLoader"]; vae = by_type["VAELoader"]; unet = by_type["UNETLoader"]
    latent = by_type["EmptyLatentImage"]; sampler = by_type["KSampler"]
    encodes = [node for node in nodes.values() if node.get("type") == "CLIPTextEncode"]
    if len(encodes) < 2:
        raise ValueError("Anima GUI export must contain positive and negative CLIPTextEncode nodes")
    negative_node = next((n for n in encodes if "score_1" in str(_widget(n, "text", ""))), encodes[0])
    positive_node = next((n for n in encodes if n["id"] != negative_node["id"]), encodes[1])
    decode = by_type["VAEDecode"]
    positive_text = prompt if prompt is not None else _widget(positive_node, "text", "")
    negative_text = negative_prompt if negative_prompt is not None else _widget(negative_node, "text", "")
    width_value = int(width if width is not None else _widget(latent, "width", 1024))
    height_value = int(height if height is not None else _widget(latent, "height", 1024))
    seed_value = int(seed if seed is not None else _widget(sampler, "seed", 0))
    api: dict[str, Any] = {
        str(clip["id"]): {"class_type": "CLIPLoader", "inputs": {"clip_name": _widget(clip, "clip_name"), "type": _widget(clip, "type", "stable_diffusion"), "device": _widget(clip, "device", "default")}},
        str(vae["id"]): {"class_type": "VAELoader", "inputs": {"vae_name": _widget(vae, "vae_name")}},
        str(unet["id"]): {"class_type": "UNETLoader", "inputs": {"unet_name": _widget(unet, "unet_name"), "weight_dtype": _widget(unet, "weight_dtype", "default")}},
        str(latent["id"]): {"class_type": "EmptyLatentImage", "inputs": {"width": width_value, "height": height_value, "batch_size": int(_widget(latent, "batch_size", 1))}},
        str(negative_node["id"]): {"class_type": "CLIPTextEncode", "inputs": {"text": negative_text, "clip": [str(clip["id"]), 0]}},
        str(positive_node["id"]): {"class_type": "CLIPTextEncode", "inputs": {"text": positive_text, "clip": [str(clip["id"]), 0]}},
        str(sampler["id"]): {"class_type": "KSampler", "inputs": {"seed": seed_value, "steps": int(_widget(sampler, "steps", 30)), "cfg": float(_widget(sampler, "cfg", 4)), "sampler_name": _widget(sampler, "sampler_name", "er_sde"), "scheduler": _widget(sampler, "scheduler", "simple"), "denoise": float(_widget(sampler, "denoise", 1.0)), "model": [str(unet["id"]), 0], "positive": [str(positive_node["id"]), 0], "negative": [str(negative_node["id"]), 0], "latent_image": [str(latent["id"]), 0]}},
        str(decode["id"]): {"class_type": "VAEDecode", "inputs": {"samples": [str(sampler["id"]), 0], "vae": [str(vae["id"]), 0]}},
    }
    save = next((n for n in gui.get("nodes", []) if n.get("type") == "SaveImage"), None)
    if save:
        api[str(save["id"])] = {"class_type": "SaveImage", "inputs": {"filename_prefix": _widget(save, "filename_prefix", "Anima"), "images": [str(decode["id"]), 0]}}
    return api


def load_and_adapt(path: str, **kwargs: Any) -> dict[str, Any]:
    import json
    value = json.loads(open(path, encoding="utf-8").read())
    return gui_to_api(value, **kwargs)
