"""Exact-execution tools for the Modal image system.

Tools are intentionally limited to operations that need binary data, API calls,
queue state, or deterministic storage. Prompt and curation procedures live in
skills/commands/agents beside this module.
"""
from __future__ import annotations
import base64, csv, hashlib, json, os, re, threading, time, urllib.request, uuid
from pathlib import Path
from typing import Any
try:
    from . import vector_store
except ImportError:  # local smoke-test loader
    import importlib.util as _importlib_util
    _vector_spec = _importlib_util.spec_from_file_location("vector_store", Path(__file__).with_name("vector_store.py"))
    vector_store = _importlib_util.module_from_spec(_vector_spec)
    assert _vector_spec.loader is not None
    _vector_spec.loader.exec_module(vector_store)

ROOT = Path(os.getenv("HERMES_HOME", str(Path.home()/".hermes"))) / "cache" / "modal-memory"
ROOT.mkdir(parents=True, exist_ok=True)
REGISTRY = ROOT / "registry.jsonl"
JOBS = ROOT / "jobs.jsonl"
DATASET = ROOT / "dataset" / "train.csv"
CACHE_DIR = ROOT / "images"
ANALYSIS_DIR = ROOT / "analysis"
LOCK = threading.RLock()
CACHE_TTL = int(os.getenv("IMAGE_CACHE_TTL_SECONDS", "86400"))
NEG_DEFAULTS = "low quality, blurry, watermark, signature, text overlay, cropped, out of frame"
STYLES = {
 "photorealistic":"photorealistic, 35mm prime lens, natural shadows, cinematic color grade",
 "cinematic":"cinematic film still, anamorphic lens flare, dramatic lighting, deep shadows",
 "anime":"vibrant Japanese anime illustration, crisp linework, soft atmospheric glow",
 "3d-render":"Unreal Engine 5 render, ray-traced reflections, dramatic studio lighting",
 "pencil-sketch":"detailed pencil sketch, fine shading, cross-hatching, graphite texture",
 "cyberpunk":"cyberpunk aesthetic, neon rain, wet streets, holographic reflections",
 "studio-portrait":"professional studio portrait, softbox lighting, Rembrandt setup, crisp eyes",
 "watercolor":"watercolor painting, flowing pigments, paper texture, dreamy atmosphere",
 "metallic":"metallic finish, chrome reflections, polished surfaces, industrial aesthetic",
 "portrait":"classic portrait photography, shallow depth of field, sharp focus on eyes",
}

def _json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists(): return []
    with LOCK: return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
def _append(path: Path, row: dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with LOCK:
        with path.open("a", encoding="utf-8") as f: f.write(json.dumps(row, ensure_ascii=False)+"\n")
def _replace(path: Path, rows: list[dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with LOCK: path.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+("\n" if rows else ""))
def _ok(**x): return json.dumps({"status":"success", **x}, ensure_ascii=False)
def _err(kind, msg, remediation): return json.dumps({"status":"error","error_type":kind,"message":msg,"remediation":remediation}, ensure_ascii=False)
def _hash(value: Any) -> str: return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def _cache_path(key: str) -> Path: return CACHE_DIR / f"{key}.json"
def _cache_get(key: str):
    p=_cache_path(key)
    if not p.exists() or time.time()-p.stat().st_mtime > CACHE_TTL: return None
    try: return json.loads(p.read_text())
    except Exception: return None
def _cache_put(key: str, value: dict[str,Any]): CACHE_DIR.mkdir(parents=True,exist_ok=True); _cache_path(key).write_text(json.dumps(value,ensure_ascii=False))
def _prompt(a: dict[str,Any]) -> str:
    p=str(a.get("prompt","")).strip(); seed=int(a.get("seed",0) or 0)
    p=re.sub(r"\{([^{}]+)\}",lambda m:m.group(1).split("|")[seed%len(m.group(1).split("|"))] if "|" in m.group(1) else m.group(0),p)
    p=re.sub(r"\^([0-9.]+)",lambda m:f":{max(.5,min(2.,float(m.group(1))))}",p)
    style=a.get("style");
    if style in STYLES:p=f"{p}, {STYLES[style]}"
    return " ".join(p.split())
def _post(url: str, payload: dict[str,Any], timeout=900):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read())

def record_audit(tool_name: str, args: dict[str, Any] | None = None) -> None:
    """Write metadata only; never persist prompts or image bytes in the audit log."""
    _append(ROOT / "audit.jsonl", {"timestamp": time.time(), "tool": tool_name, "argument_keys": sorted((args or {}).keys())})

def prepare_prompt_tool(a, **kw):
    return _ok(prompt=_prompt(a),negative_prompt=", ".join(filter(None,[a.get("negative_prompt",""),NEG_DEFAULTS])),operations=["inline_vars","weight_clamp","style_suffix","negative_defaults"])
def enhance_prompt(a, **kw):
    p=_prompt(a); return _ok(enhanced_prompt=p,engine="deterministic-template",instruction={"system":"Preserve every user detail; add only camera, lighting, atmosphere.","user_message":p})
def list_styles(a, **kw): return _ok(styles={k:{"description":v,"prompt_suffix":v,"neg_defaults":["universal"]} for k,v in STYLES.items()})
def get_prompt_catalog(a, **kw):
    return _ok(catalog={"styles":list(STYLES),"aspect_ratios":["landscape","square","portrait"],"entity_types":["image","prompt","style","template","category"],"weight_range":[.5,2.],"cache_ttl_seconds":CACHE_TTL})
def generate_from_template(a, **kw):
    templates={"character_scene":"{character} in {location} during {season}, {style}","product_shot":"{product} on {surface}, {lighting}, commercial product photography","story_panel":"{shot_type} of {character} {action}, {mood}, {style}"}; name=a.get("template_name","character_scene"); template=a.get("inline_template") or templates.get(name)
    if not template:return _err("entry_not_found","Template not found","Use character_scene, product_shot, or story_panel.")
    ctx=a.get("context") or {}; filled=template
    for k,v in ctx.items():filled=filled.replace("{"+k+"}",str(v))
    return _ok(mode=a.get("mode","render"),filled_prompt=filled,slot_values=ctx,instruction={"template":name,"lists":{}})
def create_image(a, **kw):
    endpoint=os.getenv("MODAL_BACKEND_URL"); executed=_prompt(a); negative=", ".join(filter(None,[a.get("negative_prompt",""),NEG_DEFAULTS])); payload={"prompt":executed,"negative_prompt":negative,"model":a.get("model","qwen-image"),"aspect_ratio":a.get("aspect_ratio","1:1"),"params":a.get("params",{}),"async":bool(a.get("async",False))}
    key=_hash(payload); cached=_cache_get(key)
    if cached:return _ok(**cached,from_cache=True,cache_key=key)
    if not endpoint:return _err("missing_credentials","MODAL_BACKEND_URL is not configured","Set the deployed Modal generate endpoint.")
    try:
        result=_post(endpoint,payload)
        if result.get("status")=="error":return json.dumps(result,ensure_ascii=False)
        result.update({"executed_prompt":executed,"negative_prompt":negative,"cache_key":key})
        if not result.get("job_id"):_cache_put(key,result)
        return _ok(**result,from_cache=False)
    except Exception as exc:return _err("generation_failed",str(exc),"Inspect Modal and ComfyUI logs; validate workflow JSON.")
def analyze_image(a, **kw):
    """Binary image operation: Modal vision endpoint first, local metadata fallback."""
    raw=a.get("image_b64",""); url=os.getenv("MODAL_ANALYZE_URL") or (os.getenv("MODAL_BACKEND_URL","").rstrip("/")+"/analyze" if os.getenv("MODAL_BACKEND_URL") else "")
    if not raw and not a.get("image_url"):return _err("invalid_parameter","image_b64 or image_url is required","Provide an image input.")
    key=_hash({"image":raw[:80],"url":a.get("image_url"),"task":a.get("task","caption")}); cached=_cache_get("analysis-"+key)
    if cached:return _ok(**cached,from_cache=True)
    try:
        if url:
            result=_post(url,{"image_b64":raw,"image_url":a.get("image_url"),"task":a.get("task","caption")},timeout=300)
        else:
            from PIL import Image
            image=Image.open(__import__("io").BytesIO(base64.b64decode(raw))); result={"width":image.width,"height":image.height,"format":image.format,"mode":image.mode,"caption":None,"note":"Set MODAL_ANALYZE_URL for semantic captioning."}
        _cache_put("analysis-"+key,result); return _ok(**result,from_cache=False,analysis_key=key)
    except Exception as exc:return _err("analysis_failed",str(exc),"Check image encoding and the Modal vision endpoint.")
def queue_image(a, **kw):
    endpoint=os.getenv("MODAL_QUEUE_URL")
    if not endpoint:return _err("missing_credentials","MODAL_QUEUE_URL is not configured","Set the deployed Modal queue endpoint.")
    payload={"prompt":_prompt(a),"negative_prompt":a.get("negative_prompt",NEG_DEFAULTS),"model":a.get("model","qwen-image"),"aspect_ratio":a.get("aspect_ratio","1:1"),"params":a.get("params",{})}
    try:
        result=_post(endpoint,payload,timeout=120); job_id=result.get("job_id")
        if job_id:_append(JOBS,{"job_id":job_id,"status":"queued","created_at":time.time(),"model":payload["model"]})
        return _ok(**result)
    except Exception as exc:return _err("queue_error",str(exc),"Inspect the Modal queue endpoint and ComfyUI worker.")
def get_job(a, **kw):
    job_id=a.get("job_id"); endpoint=os.getenv("MODAL_JOB_STATUS_URL")
    if endpoint:
        try:return _ok(**_post(endpoint,{"job_id":job_id},timeout=60))
        except Exception as exc:return _err("queue_error",str(exc),"Inspect the Modal status endpoint.")
    hit=next((x for x in reversed(_json_lines(JOBS)) if x.get("job_id")==job_id),None); return _ok(**hit) if hit else _err("entry_not_found","Job not found","Call queue_image and retain its job_id.")
def cancel_job(a, **kw):
    endpoint=os.getenv("MODAL_JOB_CANCEL_URL");
    if endpoint:
        try:return _ok(**_post(endpoint,{"job_id":a.get("job_id")},timeout=30))
        except Exception as exc:return _err("queue_error",str(exc),"Inspect Modal queue logs.")
    return _err("queue_unavailable","Cancellation endpoint is not configured","Set MODAL_JOB_CANCEL_URL.")
def cache_stats(a, **kw):
    files=list(CACHE_DIR.glob("*.json")); fresh=sum(1 for p in files if time.time()-p.stat().st_mtime<=CACHE_TTL); return _ok(total=len(files),fresh=fresh,expired=len(files)-fresh,ttl_seconds=CACHE_TTL,location=str(CACHE_DIR))
def cache_clear(a, **kw):
    if a.get("key"):
        p=_cache_path(a["key"]); p.unlink(missing_ok=True); return _ok(cleared=[a["key"]])
    if not a.get("confirm"):return _err("invalid_parameter","confirm=true is required for clearing all cache","Retry with confirm=true.")
    removed=0
    for p in CACHE_DIR.glob("*.json"):p.unlink();removed+=1
    return _ok(cleared_count=removed)
def register_entity(a, **kw):
    entry={"id":_hash({**a,"time":time.time()})[:16],"entity_type":a.get("entity_type","prompt"),"keyword":a.get("keyword"),"prompt_text":a.get("prompt_text"),"image_file":a.get("image_file"),"style":a.get("style"),"tags":a.get("tags",[]),"votes_up":1 if a.get("liked",True) else 0,"votes_down":0,"is_negative":False,"created_at":time.time(),"usage_count":0}; _append(REGISTRY,entry); return _ok(entry=entry)
def list_entities(a, **kw):
    rows=_json_lines(REGISTRY); typ=a.get("entity_type"); rows=[x for x in rows if not typ or x.get("entity_type")==typ]; return _ok(total=len(rows),results=rows[:int(a.get("limit",50))])
def get_entity(a, **kw):
    hit=next((x for x in _json_lines(REGISTRY) if x.get("id")==a.get("id") or x.get("keyword")==a.get("keyword")),None); return _ok(entry=hit) if hit else _err("entry_not_found","No matching registry entry","Use list_entities first.")
def semantic_search(a, **kw):
    q=str(a.get("query_text","")).lower(); rows=[]
    for x in _json_lines(REGISTRY):
        text=(x.get("prompt_text") or "").lower(); score=sum(1 for w in q.split() if w in text)/max(1,len(q.split())); rows.append({**x,"score":round(score,4),"ranked_score":round(score+.01*x.get("votes_up",0),4)})
    return _ok(results=sorted(rows,key=lambda x:x["ranked_score"],reverse=True)[:int(a.get("top_k",5))])
def upsert_embedding(a, **kw):
    try:
        result=vector_store.upsert_memory(text=a.get("text") or a.get("prompt_text") or "", vector=a.get("vector"), entity_id=a.get("entity_id") or a.get("id"), entity_type=a.get("entity_type","prompt"), style=a.get("style",""), image_file=a.get("image_file",""), metadata=a.get("metadata"), model=a.get("embedding_model")); return _ok(**result)
    except Exception as exc:return _err("vector_store_error",str(exc),"Install lancedb and configure an embedding provider or pass vector explicitly.")
def vector_search(a, **kw):
    try:
        result=vector_store.search_memory(query_text=a.get("query_text"), query_vector=a.get("query_vector"), top_k=a.get("top_k",5), entity_type=a.get("entity_type"), style=a.get("style"), include_vector=bool(a.get("include_vector",False))); return _ok(results=result,top_k=int(a.get("top_k",5)),backend="lancedb")
    except Exception as exc:return _err("vector_search_error",str(exc),"Configure MODAL_EMBED_TEXT_URL or install sentence-transformers and lancedb.")
def vector_stats(a, **kw):
    try:return _ok(**vector_store.stats(),backend="lancedb")
    except Exception as exc:return _err("vector_store_error",str(exc),"Install lancedb and check VECTOR_DB_PATH.")
def export_vectors(a, **kw):
    try:return _ok(**vector_store.export_jsonl(a.get("path",str(ROOT/"exports"/"vectors.jsonl")),bool(a.get("include_vectors",True))),backend="lancedb")
    except Exception as exc:return _err("vector_export_error",str(exc),"Check the vector store path and permissions.")
def import_vectors(a, **kw):
    try:return _ok(**vector_store.import_jsonl(a.get("path"),bool(a.get("replace",False))),backend="lancedb")
    except Exception as exc:return _err("vector_import_error",str(exc),"Provide a JSONL export containing id, text, and vector fields.")
def delete_embedding(a, **kw):
    try:return _ok(**vector_store.delete_memory(a.get("entity_id") or a.get("id")),backend="lancedb")
    except Exception as exc:return _err("vector_delete_error",str(exc),"Provide an entity_id and check VECTOR_DB_PATH.")
def vote_entry(a, **kw):
    rows=_json_lines(REGISTRY); hit=next((x for x in rows if x.get("id")==a.get("entry_id")),None)
    if not hit:return _err("entry_not_found","Entry not found","Use list_entities.")
    key="votes_up" if a.get("vote","up")=="up" else "votes_down";hit[key]=hit.get(key,0)+1;hit["is_negative"]=hit.get("votes_down",0)>=3;_replace(REGISTRY,rows);return _ok(entry=hit)
def save_as_reference(a, **kw): a={**a,"entity_type":"image","prompt_text":a.get("prompt"),"keyword":a.get("keyword")}; result=json.loads(register_entity(a));result["memory_type"]="liked_reference";return json.dumps(result,ensure_ascii=False)
def export_for_generation(a, **kw):
    result=json.loads(get_entity(a)); hit=result.get("entry"); return _ok(reference_url=hit.get("image_file") if hit else None,recommended_prompt=hit.get("prompt_text") if hit else "",usage_note="Use reference for style/lighting only; preserve the new subject.")
def upload_asset(a, **kw):
    raw=base64.b64decode(a.get("image_b64","")); name=a.get("image_name") or f"asset-{_hash(time.time())[:8]}.png"; path=ROOT/"assets"/str(a.get("collection_name","default"))/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);return _ok(rel_path=str(path.relative_to(ROOT)),public_url=f"file://{path}",data_uri="data:image/png;base64,"+base64.b64encode(raw).decode())
def save_training_pair(a, **kw):
    DATASET.parent.mkdir(parents=True,exist_ok=True); new=not DATASET.exists()
    with DATASET.open("a",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        if new:w.writerow(["timestamp","executed_prompt","raw_user_concept","image_file","style","negative_prompt","tags","model","quality_score"])
        w.writerow([time.time(),a.get("prompt",""),a.get("raw_user_concept",""),a.get("image_file",""),a.get("style",""),a.get("negative_prompt",""),json.dumps(a.get("tags",[])),a.get("model",""),a.get("quality_score","")])
    return _ok(dataset_location=str(DATASET),dataset_row=True)
def export_dataset_manifest(a, **kw): return _ok(total_pairs=max(0,len(DATASET.read_text().splitlines())-1) if DATASET.exists() else 0,files=[str(DATASET)] if DATASET.exists() else [],dataset_location=str(DATASET),hf_dataset_repo=os.getenv("HF_DATASET_REPO"))
def sync_hf_dataset(a, **kw): return _hf_sync("dataset",DATASET,a)
def sync_hf_model(a, **kw): return _hf_sync("model",Path(a.get("local_dir",ROOT)),a)
def _hf_sync(kind: str, path: Path, a: dict[str,Any]):
    repo=a.get("repo_id") or os.getenv("HF_DATASET_REPO" if kind=="dataset" else "HF_MODEL_REPO"); token=os.getenv("HF_TOKEN")
    if not repo or not token:return _err("missing_credentials","HF repo_id and HF_TOKEN are required","Set HF_TOKEN and HF_DATASET_REPO/HF_MODEL_REPO or pass repo_id.")
    try:
        from huggingface_hub import HfApi
        api=HfApi(token=token); api.create_repo(repo_id=repo,repo_type="dataset" if kind=="dataset" else "model",exist_ok=True); api.upload_folder(folder_path=str(path.parent if path.is_file() else path),repo_id=repo,repo_type="dataset" if kind=="dataset" else "model",path_in_repo=path.name if path.is_file() else "",commit_message=f"sync modal-memory {kind}")
        return _ok(repo_id=repo,repo_type=kind,source=str(path),url=f"https://huggingface.co/{repo}")
    except Exception as exc:return _err("registry_unavailable",str(exc),"Install huggingface_hub and verify the token/repository permissions.")
def learn_style(a, **kw):
    rows=[x for x in _json_lines(REGISTRY) if x.get("style")==a.get("style") and not x.get("is_negative")]; suffix=STYLES.get(a.get("style"),""); return _ok(style=a.get("style"),samples=len(rows),learned_suffix=suffix,positive_examples=rows[:int(a.get("top_k",5))],method="votes+registry; add embeddings for semantic ranking")
def load_model(a, **kw): return _ok(model_id=a.get("model_id","qwen-image"),message="Workflow/model selection is configured on Modal.",details={"lora_path":a.get("lora_path")})
def edit_image(a, **kw): return _err("modality_unsupported","Default workflow is text-only","Configure an edit-capable ComfyUI workflow.")
def upscale_image(a, **kw): return _err("provider_not_registered","Upscale workflow is not configured","Add an upscale workflow to the Modal data Volume.")
def convert_image_format(a, **kw): return _ok(image_b64=a.get("b64_image"),format=a.get("export_format","png"))

HANDLERS={name:globals()[name] for name in ["prepare_prompt_tool","enhance_prompt","list_styles","get_prompt_catalog","generate_from_template","create_image","analyze_image","queue_image","get_job","cancel_job","cache_stats","cache_clear","register_entity","list_entities","get_entity","semantic_search","upsert_embedding","vector_search","vector_stats","export_vectors","import_vectors","delete_embedding","vote_entry","save_as_reference","export_for_generation","upload_asset","save_training_pair","export_dataset_manifest","sync_hf_dataset","sync_hf_model","learn_style","load_model","edit_image","upscale_image","convert_image_format"]}
