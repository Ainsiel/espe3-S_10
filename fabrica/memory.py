"""MemoryGate con scope, TTL, confidence, taint y aprobacion."""

from __future__ import annotations

from typing import Any

from .storage import FactoryStorage


class MemoryGate:
    def __init__(self, storage: FactoryStorage) -> None:
        self.storage = storage

    def read_filtered(self, agent_id: str, scopes: tuple[str, ...]) -> dict[str, Any]:
        records = self._load_records()
        approved = self.filter_records(records, agent_id=agent_id, scopes=scopes)
        return {
            "agent_id": agent_id,
            "records": approved,
            "policy": "approved_only_clean_non_expired",
            "ledgers": {scope: str(path.resolve()) for scope, path in self.storage.memory_ledger_paths().items()},
        }

    def filter_records(self, records: list[dict[str, Any]], *, agent_id: str, scopes: tuple[str, ...]) -> list[dict[str, Any]]:
        allowed: list[dict[str, Any]] = []
        for record in records:
            if record.get("scope") not in scopes:
                continue
            if record.get("approval_status") != "approved":
                continue
            if record.get("taint_status") != "clean":
                continue
            if record.get("ttl") in ("expired", "P0D"):
                continue
            if record.get("agent_id") and record.get("agent_id") != agent_id:
                continue
            allowed.append(record)
        return allowed

    def propose(self, proposal: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            "memory_id": proposal.get("memory_id", "MEM-PROPOSED"),
            "scope": proposal.get("scope", "project"),
            "content": proposal.get("content", "TBD"),
            "source_id": proposal.get("source_id", "SRC-TBD"),
            "evidence_id": proposal.get("evidence_id", "EV-TBD"),
            "ttl": proposal.get("ttl", "P30D"),
            "confidence": proposal.get("confidence", 0.5),
            "taint_status": proposal.get("taint_status", "clean"),
            "approval_status": "proposed",
            "rollback_id": proposal.get("rollback_id", "RB-TBD"),
        }
        return normalized

    def _load_records(self) -> list[dict[str, Any]]:
        # La implementacion inicial mantiene Aprendizaje.md como tabla Markdown;
        # no promueve memoria automaticamente. Los registros aprobados se cargan
        # desde ledgers JSON separados por scope si un humano los crea.
        records: list[dict[str, Any]] = []
        for scope, path in self.storage.memory_ledger_paths().items():
            scoped_records = self.storage.read_json(path, default=[]) or []
            for record in scoped_records:
                records.append({**record, "scope": record.get("scope", scope), "memory_ledger_scope": scope})
        return records

