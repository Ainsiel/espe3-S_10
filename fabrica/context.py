"""RAG local deterministico: index, cache, chunks, evidencia y compactacion."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .cache import CacheManager
from .constants import PROMPT_INJECTION_PATTERNS, RAG_INDEX_VERSION
from .hashing import hash_obj, sha256_file, sha256_text, short_hash
from .storage import FactoryStorage


TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+")


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in TOKEN_RE.findall(text))


def has_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in PROMPT_INJECTION_PATTERNS)


class IndexManager:
    def __init__(self, storage: FactoryStorage, cache: CacheManager) -> None:
        self.storage = storage
        self.cache = cache
        self.index_path = ".fabrica/index/index.json"

    def authorized_source_paths(self) -> list[Path]:
        allowed_suffixes = {".md", ".py", ".json", ".toml", ".yml", ".yaml"}
        excluded_dirs = {".fabrica", "__pycache__", ".git", "agent-logs", "tool-logs", "reports"}
        paths: list[Path] = []
        for path in self.storage.root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in excluded_dirs for part in path.relative_to(self.storage.root).parts):
                continue
            if path.suffix.lower() not in allowed_suffixes:
                continue
            paths.append(path)
        return sorted(paths, key=lambda item: str(item.relative_to(self.storage.root)))

    def build(self) -> dict[str, Any]:
        sources = []
        chunks = []
        for source_index, path in enumerate(self.authorized_source_paths(), start=1):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            source_id = f"SRC-{source_index:04d}-{sha256_file(path).split(':', 1)[1][:8]}"
            relative = str(path.relative_to(self.storage.root))
            sources.append({"source_id": source_id, "path": relative, "hash": sha256_file(path)})
            for chunk_index, chunk in enumerate(self._chunk_text(text), start=1):
                content = chunk["content"]
                chunks.append(
                    {
                        "source_id": source_id,
                        "chunk_id": f"CH-{chunk_index:04d}",
                        "path": relative,
                        "lines": chunk["lines"],
                        "metadata": {"suffix": path.suffix.lower()},
                        "hash": sha256_text(content),
                        "tokens": tokenize(content),
                        "content": content,
                    }
                )
        corpus_hash = hash_obj([(source["path"], source["hash"]) for source in sources])
        index = {
            "index_version": RAG_INDEX_VERSION,
            "corpus_hash": corpus_hash,
            "sources": sources,
            "chunks": chunks,
        }
        self.storage.write_json(self.index_path, index)
        return index

    def load_or_build(self) -> dict[str, Any]:
        index = self.storage.read_json(self.index_path, default=None)
        if not index:
            return self.build()
        return index

    def query(self, query: str, *, limit: int = 6, score_threshold: float = 0.0) -> dict[str, Any]:
        index = self.load_or_build()
        cache_key = self.cache.key(
            "retrieval",
            {
                "query": query,
                "corpus_hash": index["corpus_hash"],
                "limit": limit,
                "score_threshold": score_threshold,
            },
        )
        cached = self.cache.get(cache_key)
        if cached:
            cached["cache_hit"] = True
            return cached
        query_tokens = set(tokenize(query))
        candidates: list[dict[str, Any]] = []
        seen_hashes: set[str] = set()
        for chunk in index["chunks"]:
            token_set = set(chunk["tokens"])
            overlap = len(query_tokens & token_set)
            exact_bonus = 1 if query.lower() in chunk["content"].lower() else 0
            score = (overlap + exact_bonus) / max(1, len(query_tokens))
            if score < score_threshold:
                continue
            if chunk["hash"] in seen_hashes:
                continue
            seen_hashes.add(chunk["hash"])
            rerank_score = score
            candidates.append(
                {
                    "source_id": chunk["source_id"],
                    "chunk_id": chunk["chunk_id"],
                    "path": chunk["path"],
                    "lines": chunk["lines"],
                    "metadata": chunk["metadata"],
                    "score": round(score, 6),
                    "rerank_score": round(rerank_score, 6),
                    "hash": chunk["hash"],
                    "reason_included": "keyword_overlap_fixed_rerank",
                    "content": chunk["content"],
                }
            )
        candidates.sort(key=lambda item: (-item["rerank_score"], item["path"], item["chunk_id"]))
        result = {
            "query_hash": sha256_text(query),
            "index_version": index["index_version"],
            "corpus_hash": index["corpus_hash"],
            "chunks": candidates[:limit],
            "excluded": [],
            "cache_hit": False,
        }
        self.cache.set(cache_key, result)
        return result

    def stats(self) -> dict[str, Any]:
        path = self.storage.path(self.index_path)
        index = self.storage.read_json(self.index_path, default={}) or {}
        chunks = index.get("chunks", [])
        return {
            "path": str(path.resolve()),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "index_version": index.get("index_version"),
            "corpus_hash": index.get("corpus_hash"),
            "source_count": len(index.get("sources", [])),
            "chunk_count": len(chunks),
            "avg_chunk_chars": round(sum(len(chunk.get("content", "")) for chunk in chunks) / max(1, len(chunks)), 2),
        }

    def _chunk_text(self, text: str, *, max_chars: int = 1400) -> list[dict[str, str]]:
        lines = []
        for original in text.splitlines():
            if len(original) <= max_chars:
                lines.append(original)
                continue
            for start in range(0, len(original), max_chars):
                lines.append(original[start : start + max_chars])
        chunks: list[dict[str, str]] = []
        current: list[str] = []
        start_line = 1
        for idx, line in enumerate(lines, start=1):
            heading_break = line.startswith("#") and current
            size_break = sum(len(item) + 1 for item in current) + len(line) > max_chars
            if heading_break or size_break:
                chunks.append({"lines": f"{start_line}-{idx - 1}", "content": "\n".join(current).strip()})
                current = []
                start_line = idx
            current.append(line)
        if current:
            chunks.append({"lines": f"{start_line}-{len(lines)}", "content": "\n".join(current).strip()})
        return [chunk for chunk in chunks if chunk["content"]]


class ContextManager:
    def __init__(self, storage: FactoryStorage, index: IndexManager) -> None:
        self.storage = storage
        self.index = index

    def build_minimal_context(self, agent_id: str, state: dict[str, Any], purpose: str) -> dict[str, Any]:
        objective = state.get("work_order", {}).get("objective", "")
        query = f"{state.get('phase')} {agent_id} {purpose} {objective}"
        raw = self.index.query(query, limit=6, score_threshold=0.0)
        included = []
        excluded = list(raw.get("excluded", []))
        for chunk in raw["chunks"]:
            if has_prompt_injection(chunk["content"]):
                excluded.append({**chunk, "reason": "tainted"})
                continue
            included.append(chunk)
        context_pack = {
            "context_pack_id": "CTX-" + short_hash({"agent_id": agent_id, "query_hash": raw["query_hash"], "chunks": [c["hash"] for c in included]}),
            "query_hash": raw["query_hash"],
            "created_at": "2026-06-08T00:00:00Z",
            "index_version": raw["index_version"],
            "corpus_hash": raw["corpus_hash"],
            "reranker_version": "fixed-keyword-overlap-1.0",
            "score_threshold": 0.0,
            "chunks": included,
            "excluded": [
                {
                    "source_id": item.get("source_id", "SRC-TBD"),
                    "chunk_id": item.get("chunk_id", "CH-TBD"),
                    "reason": item.get("reason", "not_relevant"),
                }
                for item in excluded
            ],
        }
        self.storage.write_json("context-pack.json", context_pack)
        self.storage.write_json(self.storage.run_dir / "context-pack.json", context_pack)
        evidence = self.evidence_from_context(context_pack)
        self.storage.write_json("evidence-register.json", evidence)
        return context_pack

    def evidence_from_context(self, context_pack: dict[str, Any]) -> list[dict[str, Any]]:
        evidence = []
        for idx, chunk in enumerate(context_pack.get("chunks", []), start=1):
            evidence.append(
                {
                    "evidence_id": f"EV-{idx:04d}-{chunk['hash'].split(':', 1)[1][:8]}",
                    "source_id": chunk["source_id"],
                    "chunk_id": chunk["chunk_id"],
                    "path": str((self.storage.root / chunk["path"]).resolve()),
                    "commit": "no-git",
                    "hash": chunk["hash"],
                    "lines": chunk.get("lines", "TBD"),
                    "claim_supported": "Contexto autorizado para decision critica del run.",
                    "trust": "trusted",
                }
            )
        return evidence
