from __future__ import annotations
import pathlib, re, sys
root=pathlib.Path(__file__).parents[1]/"skills"
required={"visual-production-router","image-generation","photo-restoration","nothing-design","memory-recall","prompt-engineer","character-story-video","meme-generator","video-generator"}
found={p.name for p in root.iterdir() if p.is_dir()}
missing=required-found
if missing: raise SystemExit(f"missing skills: {sorted(missing)}")
for name in sorted(required):
    p=root/name/"SKILL.md"; text=p.read_text()
    if not text.startswith("---\n") or text.count("---")<2: raise SystemExit(f"invalid frontmatter: {p}")
    if len(text.splitlines())>=500: raise SystemExit(f"skill too long; move detail to references: {p}")
    if not re.search(r"^name:\s*\S+",text,re.M) or not re.search(r"^description:\s*.+",text,re.M): raise SystemExit(f"missing metadata: {p}")
    for ref in re.findall(r"`(references/[^`]+)`",text):
        if not (root/name/ref).exists(): print(f"warning: missing referenced resource {name}/{ref}")
    print("SKILL OK",name)
print("SKILL PACK VALID")
