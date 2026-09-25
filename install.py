"""Cross-platform installer.

Linux/macOS: python3 install.py [--home ~/.hermes]
Windows:      py install.py [--home %USERPROFILE%\\.hermes]
"""
from __future__ import annotations
import argparse, json, os, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLUGIN = ROOT / "plugins" / "image_gen" / "modal-memory"

def main():
    p=argparse.ArgumentParser(); p.add_argument("--home", default=os.getenv("HERMES_HOME", str(Path.home()/".hermes"))); p.add_argument("--claude", action="store_true", help="also install the Claude Code plugin"); args=p.parse_args()
    home=Path(args.home).expanduser(); dest=home/"plugins"/"image_gen"/"modal-memory"; dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists(): shutil.rmtree(dest)
    shutil.copytree(PLUGIN,dest,ignore=shutil.ignore_patterns("__pycache__"))
    print(f"Installed Hermes plugin: {dest}")
    print("Set MODAL_BACKEND_URL and optionally HF_TOKEN/HF_MODEL_REPO/HF_DATASET_REPO.")
    if args.claude:
        claude=home/"plugins"/"claude"/"modal-memory"; claude.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(ROOT/"claude-plugin",claude,dirs_exist_ok=True)
        print(f"Installed Claude Code plugin: {claude}")
    print("Next: configure image_gen.provider=modal, then run the included status command.")
if __name__ == "__main__": main()
