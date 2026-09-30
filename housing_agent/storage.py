"""Small immutable-run and JSON utilities; no credentials are persisted."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_inventory(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): sha256_bytes(p.read_bytes())
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    }


def verify_inventory(root: Path, manifest: dict) -> None:
    for relative, expected in manifest.get("files", {}).items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Unsafe path in run manifest")
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            raise ValueError(f"Missing or changed run artifact: {relative}")
    if not manifest.get("files"):
        raise ValueError("Run manifest has no file checksums")
