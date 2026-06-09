"""Evals deterministicas de fabrica."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .frontend import audit_contrast, validate_design_tokens
from .harness import HarnessRunner
from .orchestrator import OrchestratorGraph
from .policy import PolicyEngine
from .storage import FactoryStorage


class EvalRunner:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run(self) -> dict[str, Any]:
        cases = [
            self._eval_unknown_agent,
            self._eval_action_without_approval,
            self._eval_repeated_route_stability,
            self._eval_frontend_quality_contract,
        ]
        results = [case() for case in cases]
        return {
            "eval_set_version": "eval-set-arnes-1.0",
            "status": "complete" if all(result["passed"] for result in results) else "error",
            "evals_total": len(results),
            "evals_passed": sum(1 for result in results if result["passed"]),
            "reproducibility_practical_percentage": 100 if all(result["passed"] for result in results) else 0,
            "results": results,
        }

    def _eval_unknown_agent(self) -> dict[str, Any]:
        with TemporaryDirectory() as tmp:
            storage = FactoryStorage(Path(tmp))
            storage.ensure_layout()
            harness = HarnessRunner(storage)
            state = {
                "run_id": "RUN-EVAL",
                "cycle_id": "CYC-EVAL",
                "task_id": "TASK-EVAL",
                "phase": "eval",
                "status": "complete",
                "input_hash": "sha256:eval",
                "budget": {},
                "approval": {"status": "none"},
                "work_order": storage.default_work_order(),
                "outputs": {},
                "evidence": [],
                "project_path": str(storage.project_path),
            }
            result = harness.run_agent("agent.unknown", state)
            return {"eval_id": "E06", "name": "unknown_agent_blocked", "passed": result["status"] == "error"}

    def _eval_action_without_approval(self) -> dict[str, Any]:
        decision = PolicyEngine().evaluate_requested_action("deploy", "none")
        return {"eval_id": "E08", "name": "side_effect_requires_approval", "passed": decision["status"] == "needs_user_input"}

    def _eval_repeated_route_stability(self) -> dict[str, Any]:
        with TemporaryDirectory() as tmp:
            storage = FactoryStorage(Path(tmp))
            storage.ensure_layout()
            storage.write_text("01_Constitucion_y_Especificacion_Fabrica.md", "# doc\npuerta unica harness.run_agent\n")
            work_order = storage.default_work_order()
            first = OrchestratorGraph(HarnessRunner(storage)).run(work_order, str(storage.project_path))
            storage.reset_run_outputs()
            second = OrchestratorGraph(HarnessRunner(storage)).run(work_order, str(storage.project_path))
            signature_first = (first["status"], tuple(first["passed_gates"]), first["phase_count"])
            signature_second = (second["status"], tuple(second["passed_gates"]), second["phase_count"])
            return {"eval_id": "E14", "name": "repeated_runs_stable", "passed": signature_first == signature_second}

    def _eval_frontend_quality_contract(self) -> dict[str, Any]:
        tokens = validate_design_tokens()
        contrast = audit_contrast()
        return {
            "eval_id": "E16",
            "name": "frontend_tokens_and_contrast_pass",
            "passed": tokens["status"] == "pass" and contrast["status"] == "pass",
        }
