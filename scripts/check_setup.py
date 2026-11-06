#!/usr/bin/env python3
"""Small, non-destructive pre-flight check for a Divergence Engine build."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "demo_store.py",
    "soft_power_index.csv",
    "firmware/Unblocker/Unblocker.ino",
    "oled_graphics",
)


def status(ok: bool, label: str, detail: str = "") -> bool:
    mark = "OK" if ok else "CHECK"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    return ok


def read_json(url: str) -> dict | list | None:
    request = urllib.request.Request(url, headers={"User-Agent": "DivergenceEngineSetupCheck/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", choices=("pi", "jetson"), required=True)
    parser.add_argument("--skip-services", action="store_true", help="do not contact OpenNotebook or Ollama")
    args = parser.parse_args()

    failures = []
    print(f"Checking the {args.build.upper()} build in {ROOT}")

    if sys.version_info < (3, 10):
        failures.append("Python 3.10 or newer is required")
        status(False, "Python", f"found {sys.version.split()[0]}; need 3.10+")
    else:
        status(True, "Python", sys.version.split()[0])

    for relative_path in REQUIRED_FILES:
        exists = (ROOT / relative_path).exists()
        status(exists, relative_path)
        if not exists:
            failures.append(f"missing {relative_path}")

    entrypoint = ROOT / ("unblocker_pi.py" if args.build == "pi" else "diveng.py")
    exists = entrypoint.exists()
    status(exists, entrypoint.name)
    if not exists:
        failures.append(f"missing {entrypoint.name}")

    if args.build == "pi":
        present = bool(os.environ.get("MISTRAL_API_KEY", "").strip())
        status(present, "MISTRAL_API_KEY", "loaded without showing its value")
        if not present:
            failures.append("MISTRAL_API_KEY is not loaded")
    else:
        mistral_key = ROOT / "MISTRAL_API_KEY.txt"
        brave_key = ROOT / "BRAVE_SEARCH_API_KEY.txt"
        status(mistral_key.is_file() and bool(mistral_key.read_text(encoding="utf-8").strip()), "MISTRAL_API_KEY.txt")
        status(brave_key.is_file() and bool(brave_key.read_text(encoding="utf-8").strip()), "BRAVE_SEARCH_API_KEY.txt")
        if not mistral_key.is_file() or not mistral_key.read_text(encoding="utf-8").strip():
            failures.append("MISTRAL_API_KEY.txt is missing or empty")
        if not brave_key.is_file() or not brave_key.read_text(encoding="utf-8").strip():
            failures.append("BRAVE_SEARCH_API_KEY.txt is missing or empty")

    if not args.skip_services:
        notebook_url = os.environ.get("UNBLOCKER_OPEN_NOTEBOOK_API", "http://localhost:5055").rstrip("/")
        notebook = read_json(f"{notebook_url}/api/notebooks?limit=1")
        status(notebook is not None, "OpenNotebook", notebook_url)

        if args.build == "jetson":
            ollama_url = os.environ.get("UNBLOCKER_OLLAMA_API", "http://172.18.0.1:11434").rstrip("/")
            tags = read_json(f"{ollama_url}/api/tags")
            models = [model.get("name", "") for model in tags.get("models", [])] if isinstance(tags, dict) else []
            status(tags is not None, "Ollama", ollama_url)
            if tags is not None:
                status(any(name.startswith("granite-engine") for name in models), "granite chat model")
                status(any(name.startswith("granite-embedding") for name in models), "granite embedding model")

    if failures:
        print("\nFix these before launching:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nCore files and credentials are ready. Service or hardware CHECK results may be expected while disconnected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

