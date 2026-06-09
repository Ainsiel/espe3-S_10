"""Cache deterministica por hash/version/policy."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .constants import POLICY_VERSION
from .hashing import hash_obj
from .storage import FactoryStorage


class CacheManager:
    def __init__(self, storage: FactoryStorage) -> None:
        self.storage = storage
        self.cache_path = ".fabrica/cache/cache.json"

    def _load(self) -> dict[str, Any]:
        return self.storage.read_json(self.cache_path, default={}) or {}

    def _save(self, data: dict[str, Any]) -> None:
        self.storage.write_json(self.cache_path, data)

    def key(self, namespace: str, payload: Any) -> str:
        return f"{namespace}:{POLICY_VERSION}:{hash_obj(payload)}"

    def get(self, key: str) -> Any | None:
        return self._load().get(key)

    def set(self, key: str, value: Any, *, cacheable: bool = True) -> None:
        if not cacheable:
            return
        data = self._load()
        data[key] = value
        self._save(data)

    def stats(self) -> dict[str, Any]:
        data = self._load()
        path = self.storage.path(self.cache_path)
        namespaces = Counter(key.split(":", 1)[0] for key in data)
        return {
            "path": str(path.resolve()),
            "exists": path.exists(),
            "entries": len(data),
            "bytes": path.stat().st_size if path.exists() else 0,
            "namespaces": dict(sorted(namespaces.items())),
        }

