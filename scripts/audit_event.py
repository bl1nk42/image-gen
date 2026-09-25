from __future__ import annotations
import json, os, sys, time
from pathlib import Path
raw=sys.stdin.read()
try: event=json.loads(raw)
except Exception: event={"raw":raw[:2000]}
path=Path(os.getenv("HERMES_HOME",str(Path.home()/".hermes")))/"cache"/"modal-memory"/"audit.jsonl"
path.parent.mkdir(parents=True,exist_ok=True)
path.open("a",encoding="utf-8").write(json.dumps({"time":time.time(),"event":event},ensure_ascii=False)+"\n")
