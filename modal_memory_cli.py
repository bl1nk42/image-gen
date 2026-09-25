#!/usr/bin/env python3
"""CLI for Modal Memory vector store.

Examples:
  python modal_memory_cli.py status
  python modal_memory_cli.py upsert --text "cinematic neon city" --style cyberpunk
  python modal_memory_cli.py search --query "night neon city" --top-k 5
  python modal_memory_cli.py export --path ./vectors.jsonl
  python modal_memory_cli.py import --path ./vectors.jsonl --replace
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "plugins/image_gen/modal-memory"))
import vector_store


def main() -> int:
    parser = argparse.ArgumentParser(prog="modal-memory", description="LanceDB vector memory CLI")
    parser.add_argument("--db", help="LanceDB path; overrides VECTOR_DB_PATH")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show vector store status")
    up = sub.add_parser("upsert", help="embed text and store a memory")
    up.add_argument("--text", required=True); up.add_argument("--id"); up.add_argument("--type", default="prompt", dest="entity_type"); up.add_argument("--style", default=""); up.add_argument("--image-file", default="")
    search = sub.add_parser("search", help="semantic nearest-neighbor search")
    search.add_argument("--query", required=True); search.add_argument("--top-k", type=int, default=5); search.add_argument("--type", dest="entity_type"); search.add_argument("--style"); search.add_argument("--include-vector", action="store_true")
    export = sub.add_parser("export", help="export vectors and metadata as JSONL")
    export.add_argument("--path", required=True); export.add_argument("--without-vectors", action="store_true")
    imp = sub.add_parser("import", help="restore vectors and metadata from JSONL")
    imp.add_argument("--path", required=True); imp.add_argument("--replace", action="store_true")
    delete = sub.add_parser("delete", help="delete one vector memory")
    delete.add_argument("--id", required=True)
    args = parser.parse_args()
    if args.db:
        vector_store.DB_PATH = Path(args.db).expanduser()
    try:
        if args.command == "status": result = vector_store.stats()
        elif args.command == "upsert": result = vector_store.upsert_memory(text=args.text, entity_id=args.id, entity_type=args.entity_type, style=args.style, image_file=args.image_file)
        elif args.command == "search": result = {"results": vector_store.search_memory(query_text=args.query, top_k=args.top_k, entity_type=args.entity_type, style=args.style, include_vector=args.include_vector)}
        elif args.command == "export": result = vector_store.export_jsonl(args.path, include_vectors=not args.without_vectors)
        elif args.command == "import": result = vector_store.import_jsonl(args.path, replace=args.replace)
        else: result = vector_store.delete_memory(args.id)
        print(json.dumps({"status": "success", **result}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "error", "error_type": "cli_error", "message": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

if __name__ == "__main__": raise SystemExit(main())
