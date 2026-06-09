"""HarnessRunner: puerta unica de ejecucion agentica."""

from __future__ import annotations

from typing import Any

from .agents import get_agent_function
from .budget import BudgetExceeded, BudgetManager
from .cache import CacheManager
from .context import ContextManager, IndexManager
from .hashing import hash_obj
from .memory import MemoryGate
from .policy import PolicyDecision, PolicyEngine
from .pricing import PricingCatalog
from .registries import AgentRegistry, SkillRegistry, ToolRegistry
from .schemas import make_agent_output
from .storage import FactoryStorage
from .tools import ToolRunner
from .validators import ValidatorChain


class HarnessRunner:
    def __init__(self, storage: FactoryStorage) -> None:
        self.storage = storage
        self.agent_registry = AgentRegistry()
        self.tool_registry = ToolRegistry()
        self.skill_registry = SkillRegistry()
        self.policy = PolicyEngine()
        self.cache = CacheManager(storage)
        self.index = IndexManager(storage, self.cache)
        self.context = ContextManager(storage, self.index)
        self.memory = MemoryGate(storage)
        self.budget = BudgetManager(storage)
        self.validators = ValidatorChain(storage)
        self.storage.write_json("pricing-catalog.json", PricingCatalog().as_json())

    def snapshot_registries(self) -> None:
        self.storage.write_registry_snapshot(
            self.agent_registry.as_json(),
            self.tool_registry.as_json(),
            self.skill_registry.as_json(),
        )
        self.storage.write_json("pricing-catalog.json", PricingCatalog().as_json())

    def run_agent(self, agent_id: str, state: dict[str, Any]) -> dict[str, Any]:
        try:
            agent = self.agent_registry.get(agent_id)
            self.policy.assert_agent_allowed(agent, state)
            self.budget.assert_available(agent, state)
            if agent_id == "agent.orchestrator":
                raise PolicyDecision("error", "flow_only_agent_not_executable")

            context_pack = self.context.build_minimal_context(agent.agent_id, state, agent.purpose)
            evidence = self.context.evidence_from_context(context_pack)
            memory_pack = self.memory.read_filtered(agent.agent_id, agent.memory_read_scopes)
            scoped_state = {
                **state,
                "context_pack": context_pack,
                "context_evidence": evidence,
                "memory_pack": memory_pack,
            }
            tool_runner = ToolRunner(
                storage=self.storage,
                registry=self.tool_registry,
                policy=self.policy,
                cache=self.cache,
                index=self.index,
                context=self.context,
                agent=agent,
                state=scoped_state,
            )
            fn = get_agent_function(agent_id)
            raw_output = fn(scoped_state, self.storage, tool_runner)
            validation = self.validators.validate_all(raw_output, scoped_state)
            if validation["status"] != "pass":
                output = make_agent_output(
                    agent_id=agent_id,
                    task_id=state["task_id"],
                    status=validation["next_action"] if validation["next_action"] in ("needs_user_input", "not_answerable", "error") else "error",
                    summary="ValidatorChain bloqueo la salida.",
                    artifacts=raw_output.get("artifacts", []),
                    evidence=raw_output.get("evidence", []),
                    issues=validation["blocking_issues"],
                    next_action=validation["next_action"],
                )
            else:
                output = raw_output
            usage_entry = self.budget.record_agent(
                run_id=state["run_id"],
                phase=state["phase"],
                agent=agent,
                input_payload={
                    "state": {key: state[key] for key in state if key != "work_order"},
                    "context_pack_id": context_pack["context_pack_id"],
                    "memory_records": len(memory_pack["records"]),
                },
                output_payload=output,
                tool_calls=tool_runner.calls,
                api_usage=state.get("api_usage"),
                model_override=state.get("billing", {}).get("model") if state.get("api_usage") else None,
                service_tier=state.get("billing", {}).get("service_tier", "standard"),
                context=state.get("billing", {}).get("context", "short"),
                regional_uplift=state.get("billing", {}).get("regional_uplift", False),
                tool_charges_usd=state.get("billing", {}).get("tool_charges_usd", "0"),
            )
            output["usage_estimate"] = {
                "cycle_id": state["cycle_id"],
                "phase": state["phase"],
                "agent_id": agent_id,
                "input_tokens": usage_entry["input_tokens"],
                "output_tokens": usage_entry["output_tokens"],
                "billable_input_tokens": usage_entry["billable_input_tokens"],
                "cached_tokens": usage_entry["cached_tokens"],
                "reasoning_tokens": usage_entry["reasoning_tokens"],
                "visible_output_tokens": usage_entry["visible_output_tokens"],
                "usage_source": usage_entry["usage_source"],
                "estimated_cost": usage_entry["estimated_cost"],
            }
            self._log_agent_finished(agent_id, state, output, validation)
            new_state = {
                **state,
                "status": output["status"],
                "evidence": evidence,
                "outputs": {
                    **state.get("outputs", {}),
                    agent_id + ":" + state["phase"]: output,
                },
            }
            self.storage.write_state(new_state)
            return output
        except KeyError as error:
            return self._error_output(agent_id, state, "unknown_agent:" + str(error))
        except PolicyDecision as error:
            return self._error_output(agent_id, state, error.reason, status=error.status)
        except BudgetExceeded as error:
            return self._error_output(agent_id, state, str(error), status="error")
        except Exception as error:  # noqa: BLE001 - el harness normaliza fallos.
            return self._error_output(agent_id, state, type(error).__name__ + ":" + str(error), status="error")

    def _log_agent_finished(self, agent_id: str, state: dict[str, Any], output: dict[str, Any], validation: dict[str, Any]) -> None:
        event = {
            "run_id": state["run_id"],
            "cycle_id": state["cycle_id"],
            "event": "agent_finished",
            "phase": state["phase"],
            "status": output["status"],
            "output_hash": hash_obj(output),
            "evidence_ids": [item["evidence_id"] for item in output.get("evidence", [])],
            "validation_status": validation["status"],
            "usage_estimate": output.get("usage_estimate", {}),
        }
        self.storage.write_agent_log(agent_id, event)
        self.storage.write_global_log({k: v for k, v in event.items() if k != "evidence_ids"})

    def _error_output(self, agent_id: str, state: dict[str, Any], issue: str, *, status: str = "error") -> dict[str, Any]:
        normalized_status = status if status in ("needs_user_input", "not_answerable", "error") else "error"
        output = make_agent_output(
            agent_id=agent_id,
            task_id=state.get("task_id", "TASK-UNKNOWN"),
            status=normalized_status,
            summary="ARNES bloqueo la ejecucion.",
            artifacts=[],
            evidence=[
                {
                    "evidence_id": "EV-HARNESS-" + state.get("input_hash", "sha256:00000000").split(":", 1)[1][:8],
                    "source_id": "SRC-HARNESS",
                    "chunk_id": state.get("cycle_id", "CYC-UNKNOWN"),
                    "hash": state.get("input_hash", "sha256:00000000"),
                }
            ],
            issues=[issue],
            next_action=normalized_status,
        )
        self.storage.write_agent_log(
            agent_id,
            {
                "run_id": state.get("run_id", "RUN-UNKNOWN"),
                "cycle_id": state.get("cycle_id", "CYC-UNKNOWN"),
                "event": "agent_blocked",
                "phase": state.get("phase", "unknown"),
                "status": normalized_status,
                "output_hash": hash_obj(output),
                "error_code": issue,
            },
        )
        return output
