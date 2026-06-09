"""OrchestratorGraph SDD.

Durante un run, este modulo solo invoca `harness.run_agent(agent_id, state)`;
no llama tools, memoria, archivos, APIs ni agentes por fuera del harness.
"""

from __future__ import annotations

from typing import Any, Protocol

from .constants import SDD_PHASES
from .hashing import hash_obj
from .schemas import make_cycle_state


class HarnessProtocol(Protocol):
    def run_agent(self, agent_id: str, state: dict[str, Any]) -> dict[str, Any]:
        ...


FLOW: tuple[tuple[str, str], ...] = (
    ("constitution", "agent.spec"),
    ("specify", "agent.spec"),
    ("clarify", "agent.spec"),
    ("checklist", "agent.spec"),
    ("context", "agent.context_rag"),
    ("plan", "agent.architecture_plan"),
    ("plan_validation", "agent.security_policy"),
    ("plan_validation", "agent.qa"),
    ("tasks", "agent.spec"),
    ("analyze", "agent.qa"),
    ("design_system", "agent.frontend_design_system"),
    ("ux_accessibility", "agent.ux_accessibility"),
    ("implement", "agent.implementation"),
    ("validate", "agent.tests_coverage"),
    ("validate", "agent.security_policy"),
    ("validate", "agent.qa"),
    ("frontend_validate", "agent.frontend_visual_qa"),
    ("pr_deploy_gate", "agent.devops_observability"),
    ("observe", "agent.devops_observability"),
    ("observe", "agent.cost_optimizer"),
    ("close", "agent.documentation"),
    ("close", "agent.qa"),
)


class OrchestratorGraph:
    def __init__(self, harness: HarnessProtocol, *, max_steps: int = 40) -> None:
        self.harness = harness
        self.max_steps = max_steps

    def run(self, work_order: dict[str, Any], project_path: str) -> dict[str, Any]:
        input_hash = hash_obj(work_order)
        run_id = "RUN-" + input_hash.split(":", 1)[1][:12]
        outputs: dict[str, Any] = {}
        evidence: list[dict[str, Any]] = []
        passed_gates: list[str] = []
        status = "complete"
        for step_number, (phase, agent_id) in enumerate(FLOW, start=1):
            if step_number > self.max_steps:
                status = "error"
                break
            cycle_id = f"CYC-{step_number:03d}"
            state = make_cycle_state(
                run_id=run_id,
                cycle_id=cycle_id,
                task_id=f"TASK-{phase.upper()}-{step_number:03d}",
                phase=phase,
                input_hash=input_hash,
                work_order=work_order,
                project_path=project_path,
                outputs=outputs,
                evidence=evidence,
            )
            billing = work_order.get("billing", {})
            if billing:
                state["billing"] = billing
            api_usage_by_phase = work_order.get("api_usage_by_phase", {})
            api_usage = api_usage_by_phase.get(f"{phase}:{agent_id}") or api_usage_by_phase.get(phase)
            if api_usage:
                state["api_usage"] = api_usage
            state["passed_gates"] = tuple(passed_gates)
            result = self._run_with_retries(agent_id, state, max_retries=work_order.get("constraints", {}).get("max_retries", 2))
            outputs[f"{phase}:{agent_id}:{step_number}"] = result
            evidence = result.get("evidence", evidence)
            if result["status"] != "complete":
                status = result["status"]
                break
            passed_gates.append(phase)
        return {
            "run_id": run_id,
            "status": status,
            "outputs": outputs,
            "evidence": evidence,
            "passed_gates": passed_gates,
            "phase_count": len(outputs),
        }

    def _run_with_retries(self, agent_id: str, state: dict[str, Any], *, max_retries: int) -> dict[str, Any]:
        attempts = 0
        while True:
            attempts += 1
            result = self.harness.run_agent(agent_id, state)
            if result["next_action"] != "retry":
                return result
            if attempts > max_retries:
                return {
                    **result,
                    "status": "error",
                    "next_action": "error",
                    "issues": [*result.get("issues", []), "max_retries_exhausted"],
                }
