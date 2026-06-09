"""Hashing y serializacion estable."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def hash_obj(data: Any) -> str:
    return sha256_text(stable_json(data))


def short_hash(data: Any, size: int = 12) -> str:
    digest = hash_obj(data).split(":", 1)[1]
    return digest[:size]
