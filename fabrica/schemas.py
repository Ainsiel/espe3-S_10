"""Contratos de datos ejecutables para ARNES/SDD."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .constants import CLOSED_STATUSES, NEXT_ACTIONS


@dataclass(frozen=True)
class Budget:
    max_input_tokens: int = 16000
    max_output_tokens: int = 5000
    max_cost_usd: float = 0.0
    max_latency_ms: int = 120000
    max_tool_calls: int = 4
    used_input_tokens: int = 0
    used_output_tokens: int = 0
    used_tool_calls: int = 0
    estimated_cost_usd: float = 0.0


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    agent_name: str
    version: str
    status: str
    purpose: str
    single_responsibility: str
    use_when: tuple[str, ...]
    do_not_use_when: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    permissions: dict[str, bool]
    gates: tuple[str, ...]
    budget: Budget
    memory_read_scopes: tuple[str, ...]
    write_memory: bool
    evals: tuple[str, ...]
    input_schema: str = "CycleState"
    output_schema: str = "AgentOutput"
    model_policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["budget"] = asdict(self.budget)
        return data


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    purpose: str
    input_schema: str
    output_schema: str
    error_schema: str
    permissions: tuple[str, ...]
    timeout_ms: int
    retries: int
    cost: str
    side_effects: str
    sandbox: bool
    errors: tuple[str, ...]
    approval_required: bool = False
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SkillSpec:
    skill_id: str
    kind: str
    purpose: str
    tool_id: str
    input_schema: str
    output_schema: str
    deterministic: bool
    timeout_ms: int
    retry: int
    cache: bool
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_cycle_state(
    *,
    run_id: str,
    cycle_id: str,
    task_id: str,
    phase: str,
    input_hash: str,
    work_order: dict[str, Any],
    project_path: str,
    status: str = "complete",
    outputs: dict[str, Any] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    issues: list[str] | None = None,
    budget: dict[str, Any] | None = None,
    approval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in CLOSED_STATUSES:
        raise ValueError(f"Estado no permitido: {status}")
    return {
        "run_id": run_id,
        "cycle_id": cycle_id,
        "task_id": task_id,
        "phase": phase,
        "status": status,
        "input_hash": input_hash,
        "spec_hash": input_hash,
        "policy_version": "policy-arnes-1.0",
        "tool_registry_version": "tool-registry-1.0",
        "memory_version": "memory-policy-1.0",
        "evidence": evidence or [],
        "outputs": outputs or {},
        "issues": issues or [],
        "budget": budget or asdict(Budget()),
        "approval": approval or {"required": False, "status": "none"},
        "work_order": work_order,
        "project_path": project_path,
    }


def make_agent_output(
    *,
    agent_id: str,
    task_id: str,
    status: str,
    summary: str,
    artifacts: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    issues: list[str] | None = None,
    next_action: str = "continue",
    usage_estimate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in CLOSED_STATUSES:
        raise ValueError(f"Estado no permitido: {status}")
    if next_action not in NEXT_ACTIONS:
        raise ValueError(f"next_action no permitido: {next_action}")
    return {
        "agent_id": agent_id,
        "task_id": task_id,
        "status": status,
        "summary": summary,
        "artifacts": artifacts,
        "evidence": evidence,
        "issues": issues or [],
        "next_action": next_action,
        "usage_estimate": usage_estimate
        or {
            "input_tokens": 0,
            "output_tokens": 0,
            "usage_source": "pending_harness_record",
        },
    }


AGENT_OUTPUT_KEYS = {
    "agent_id",
    "task_id",
    "status",
    "summary",
    "artifacts",
    "evidence",
    "issues",
    "next_action",
    "usage_estimate",
}

TOOL_RESULT_KEYS = {
    "tool_id",
    "status",
    "input_hash",
    "output_hash",
    "side_effects",
    "sandbox",
    "latency_ms",
    "cache_hit",
    "source_ids",
    "error_code",
}
