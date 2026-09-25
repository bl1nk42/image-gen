from __future__ import annotations
import ast, importlib.util, json, pathlib, tempfile, os, subprocess, sys
root = pathlib.Path(__file__).parent
for path in [root / "modal_backend.py", root / "comfy_workflow_adapter.py", root / "test_visual_router_and_workflow.py", root / "install.py", root / "plugins/image_gen/modal-memory/__init__.py", root / "plugins/image_gen/modal-memory/tools.py"]:
    ast.parse(path.read_text())
    print("AST OK", path.relative_to(root))
cat = json.loads((root / "plugins/image_gen/modal-memory/model-catalog.json").read_text())
assert cat["version"] == 1 and cat["default_model"] == "qwen-image"
assert cat["providers"]["modal"]["models"][0]["default"] is True
assert any(model["id"] == "anima-preview" for model in cat["providers"]["modal"]["models"])
assert (root / "workflows/templates/image_anima_preview.gui.json").exists()
assert (root / "workflows/templates/image_anima_preview.manifest.json").exists()
print("CATALOG OK", cat["default_model"])
claude = json.loads((root / "claude-plugin/.claude-plugin/plugin.json").read_text())
assert claude["name"] and claude["version"]
print("CLAUDE MANIFEST OK", claude["name"])
with tempfile.TemporaryDirectory() as tmp:
    os.environ["HERMES_HOME"] = tmp
    spec = importlib.util.spec_from_file_location("memory_tools", root / "plugins/image_gen/modal-memory/tools.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    cases = {
      "get_prompt_catalog": {}, "prepare_prompt_tool": {"prompt":"{red|blue} cat^1.5", "style":"cinematic"},
      "list_styles": {}, "enhance_prompt": {"prompt":"sunset"}, "generate_from_template": {"template_name":"product_shot","context":{"product":"watch","surface":"marble","lighting":"soft"}},
      "analyze_image": {"image_b64":"not-an-image"}, "cache_stats": {}, "cache_clear": {},
      "register_entity": {"entity_type":"prompt","keyword":"test","prompt_text":"blue cat"}, "list_entities": {}, "semantic_search": {"query_text":"blue cat"},
      "save_as_reference": {"prompt":"blue cat","keyword":"cat"}, "export_dataset_manifest": {}, "learn_style": {"style":"cinematic"}, "load_model": {},
      "edit_image": {}, "upscale_image": {}, "convert_image_format": {"b64_image":"x"}
    }
    for name, args in cases.items():
        result = getattr(mod, name)(args)
        assert isinstance(result, str), (name, type(result))
        parsed = json.loads(result)
        assert parsed.get("status") in {"success", "error"}, (name, parsed)
        print("TOOL OK", name)
print("INSTALL HELP OK")
subprocess.run([sys.executable, str(root / "install.py"), "--help"], check=True, stdout=subprocess.DEVNULL)
print("ALL SMOKE TESTS PASSED")
