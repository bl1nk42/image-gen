"""Persistent vector memory for Modal Memory.

Default backend: LanceDB on a local/Modal Volume path. The table stores vectors
plus provenance metadata so results can be retrieved, exported, and restored
without regenerating embeddings. Remote embedding endpoints are optional; a
local SentenceTransformer can be used when installed.
"""
from __future__ import annotations
import csv, hashlib, json, os, shutil, time, urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(os.getenv("HERMES_HOME", str(Path.home()/".hermes"))) / "cache" / "modal-memory"
DB_PATH = Path(os.getenv("VECTOR_DB_PATH", str(ROOT / "vector_store")))
TABLE_NAME = os.getenv("VECTOR_TABLE_NAME", "memories")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:32]


def _embed_remote(url: str, text: str) -> list[float]:
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as response:
        result = json.loads(response.read())
    vector = result.get("embedding") or result.get("vector")
    if not vector: raise RuntimeError("Embedding endpoint returned no embedding/vector field")
    return [float(x) for x in vector]


def embed_text(text: str) -> tuple[list[float], str]:
    text = str(text or "").strip()
    if not text: raise ValueError("text is required for embedding")
    endpoint = os.getenv("MODAL_EMBED_TEXT_URL")
    if endpoint: return _embed_remote(endpoint, text), "modal"
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=os.getenv("HF_HOME", str(ROOT / "hf")))
        return model.encode(text, normalize_embeddings=True).astype("float32").tolist(), "local-sentence-transformer"
    except Exception as exc:
        raise RuntimeError(f"No embedding provider available: {exc}. Set MODAL_EMBED_TEXT_URL or install sentence-transformers.") from exc


def _db():
    try:
        import lancedb
    except ImportError as exc:
        raise RuntimeError("LanceDB is not installed. Install requirements-modal.txt or pip install lancedb.") from exc
    DB_PATH.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(DB_PATH))


def _table(create: bool = False, dimension: int | None = None):
    db = _db()
    names = db.table_names()
    if TABLE_NAME in names: return db.open_table(TABLE_NAME)
    if not create: return None
    if not dimension: raise ValueError("dimension is required when creating the vector table")
    return db.create_table(TABLE_NAME, data=[{"id": "__schema__", "text": "", "entity_type": "system", "style": "", "image_file": "", "metadata_json": "{}", "created_at": 0.0, "updated_at": 0.0, "embedding_model": EMBEDDING_MODEL, "embedding_provider": "schema", "vector": [0.0] * dimension}])


def upsert_memory(*, text: str, vector: list[float] | None = None, entity_id: str | None = None, entity_type: str = "prompt", style: str = "", image_file: str = "", metadata: dict[str, Any] | None = None, model: str | None = None) -> dict[str, Any]:
    if vector is None: vector, provider = embed_text(text)
    else: vector, provider = [float(x) for x in vector], "provided"
    entity_id = entity_id or _hash({"text": text, "entity_type": entity_type, "image_file": image_file})
    row = {"id": entity_id, "text": text, "entity_type": entity_type, "style": style, "image_file": image_file, "metadata_json": json.dumps(metadata or {}, ensure_ascii=False), "created_at": time.time(), "updated_at": time.time(), "embedding_model": model or EMBEDDING_MODEL, "embedding_provider": provider, "vector": vector}
    table = _table(create=True, dimension=len(vector))
    if entity_id != "__schema__":
        try: table.delete(f"id = '{entity_id}'")
        except Exception: pass
    table.add([row])
    return {"id": entity_id, "dimension": len(vector), "embedding_provider": provider, "table": TABLE_NAME, "db_path": str(DB_PATH)}


def search_memory(*, query_text: str | None = None, query_vector: list[float] | None = None, top_k: int = 5, entity_type: str | None = None, style: str | None = None, include_vector: bool = False) -> list[dict[str, Any]]:
    if query_vector is None: query_vector, _ = embed_text(query_text or "")
    table = _table()
    if table is None: return []
    query = table.search(query_vector)
    clauses = []
    if entity_type: clauses.append(f"entity_type = '{entity_type}'")
    if style: clauses.append(f"style = '{style}'")
    if clauses: query = query.where(" AND ".join(clauses))
    rows = query.limit(max(1, min(int(top_k), 100))).to_list()
    result = []
    for row in rows:
        if row.get("id") == "__schema__": continue
        item = dict(row); item["distance"] = float(item.pop("_distance", item.pop("distance", 0.0)))
        try: item["metadata"] = json.loads(item.pop("metadata_json", "{}"))
        except Exception: item["metadata"] = {}
        if not include_vector: item.pop("vector", None)
        result.append(item)
    return result


def stats() -> dict[str, Any]:
    table = _table()
    if table is None: return {"exists": False, "db_path": str(DB_PATH), "table": TABLE_NAME, "count": 0}
    count = max(0, table.count_rows() - 1)
    return {"exists": True, "db_path": str(DB_PATH), "table": TABLE_NAME, "count": count, "schema": str(table.schema)}


def export_jsonl(path: str, include_vectors: bool = True) -> dict[str, Any]:
    table = _table()
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = [] if table is None else table.to_arrow().to_pylist()
    rows = [row for row in rows if row.get("id") != "__schema__"]
    if not include_vectors:
        for row in rows: row.pop("vector", None)
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""))
    return {"path": str(target), "count": len(rows), "include_vectors": include_vectors}


def import_jsonl(path: str, replace: bool = False) -> dict[str, Any]:
    source = Path(path).expanduser()
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    valid = [row for row in rows if row.get("vector") and row.get("text") and row.get("id")]
    if not valid: raise ValueError("Import file contains no rows with id, text, and vector")
    db = _db()
    if replace and TABLE_NAME in db.table_names(): db.drop_table(TABLE_NAME)
    table = _table(create=True, dimension=len(valid[0]["vector"]))
    table.add(valid)
    return {"path": str(source), "imported": len(valid), "table": TABLE_NAME, "db_path": str(DB_PATH), "replaced": replace}


def delete_memory(entity_id: str) -> dict[str, Any]:
    table = _table()
    if table is None: return {"deleted": 0, "id": entity_id}
    table.delete(f"id = '{entity_id}'")
    return {"deleted": 1, "id": entity_id}
