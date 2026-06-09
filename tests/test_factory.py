from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fabrica.agents import AGENT_FUNCTIONS
from fabrica.constants import AGENT_IDS
from fabrica.frontend import BEST_PRACTICES_HASH, audit_contrast, validate_design_tokens
from fabrica.harness import HarnessRunner
from fabrica.memory import MemoryGate
from fabrica.orchestrator import FLOW, OrchestratorGraph
from fabrica.policy import PolicyDecision, PolicyEngine
from fabrica.pricing import PricingCatalog, normalize_usage
from fabrica.registries import AgentRegistry, SkillRegistry, ToolRegistry
from fabrica.schemas import make_agent_output, make_cycle_state
from fabrica.storage import FactoryStorage
from fabrica.validators import ValidatorChain


class FactoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.storage = FactoryStorage(self.root)
        self.storage.ensure_layout()
        for name in (
            "01_Constitucion_y_Especificacion_Fabrica.md",
            "02_Arquitectura_Stack_y_Flujos_SDD.md",
            "03_Agentes_Skills_Herramientas_y_Permisos.md",
            "04_Orquestador_Ciclo_12_Pasos_Operabilidad.md",
            "arnes.md",
            "checklist.md",
        ):
            self.storage.write_text(name, f"# {name}\nARNES harness.run_agent evidencia gates memoria cache index.\n")
        self.work_order = self.storage.default_work_order()
        self.storage.write_json("work_order.json", self.work_order)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def state(self, phase: str = "constitution") -> dict:
        return make_cycle_state(
            run_id="RUN-TEST",
            cycle_id="CYC-TEST",
            task_id="TASK-TEST",
            phase=phase,
            input_hash="sha256:11111111",
            work_order=self.work_order,
            project_path=str(self.storage.project_path),
        )

    def test_agent_registry_loads(self) -> None:
        registry = AgentRegistry()
        self.assertTrue(registry.verify_complete())
        self.assertEqual(set(registry.all()), set(AGENT_IDS))

    def test_registry_completeness(self) -> None:
        agents = AgentRegistry()
        tools = ToolRegistry()
        skills = SkillRegistry()
        self.assertTrue(tools.verify_complete())
        self.assertTrue(skills.verify_complete())
        tool_ids = set(tools.all())
        for spec in agents.all().values():
            self.assertTrue(set(spec.allowed_tools).issubset(tool_ids))

    def test_all_agent_functions_exist(self) -> None:
        expected = set(AGENT_IDS) - {"agent.orchestrator"}
        self.assertEqual(set(AGENT_FUNCTIONS), expected)

    def test_harness_rejects_unknown_agent(self) -> None:
        result = HarnessRunner(self.storage).run_agent("agent.unknown", self.state())
        self.assertEqual(result["status"], "error")
        self.assertIn("unknown_agent", result["issues"][0])

    def test_harness_applies_token_budget(self) -> None:
        state = self.state()
        state["budget"]["used_input_tokens"] = 999999
        result = HarnessRunner(self.storage).run_agent("agent.spec", state)
        self.assertEqual(result["status"], "error")
        self.assertIn("budget_exceeded", result["issues"][0])

    def test_harness_blocks_flow_only_orchestrator_agent(self) -> None:
        result = HarnessRunner(self.storage).run_agent("agent.orchestrator", self.state())
        self.assertEqual(result["status"], "error")
        self.assertIn("flow_only_agent_not_executable", result["issues"])

    def test_orchestrator_happy_path(self) -> None:
        harness = HarnessRunner(self.storage)
        harness.snapshot_registries()
        result = OrchestratorGraph(harness).run(self.work_order, str(self.storage.project_path))
        self.assertEqual(result["status"], "complete")
        self.assertTrue(self.storage.path("final-report.json").exists())
        self.assertTrue(self.storage.path("traceability-matrix.md").exists())
        self.assertTrue(self.storage.path("DESIGN_SYSTEM.md").exists())
        self.assertTrue(self.storage.path("visual-qa-report.json").exists())
        cost_report = self.storage.read_json("cost-report.json")
        self.assertIn("tool_efficiency", cost_report)
        self.assertIn("rag_index", cost_report)
        self.assertIn("cache", cost_report)
        self.assertGreaterEqual(cost_report["rag_index"]["chunk_count"], 1)
        ledger = self.storage.read_json("billing-ledger.json")
        final_report = self.storage.read_json("final-report.json")
        self.assertEqual(cost_report["model_calls"], ledger["totals"]["model_requests"])
        self.assertEqual(final_report["costs"]["totals"]["model_requests"], ledger["totals"]["model_requests"])

    def test_orchestrator_flow_is_frozen_and_harness_only(self) -> None:
        class RecordingHarness:
            def __init__(self) -> None:
                self.calls = []

            def run_agent(self, agent_id, state):
                self.calls.append((state["phase"], agent_id, state["cycle_id"]))
                return make_agent_output(
                    agent_id=agent_id,
                    task_id=state["task_id"],
                    status="complete",
                    summary="ok",
                    artifacts=[],
                    evidence=[{"evidence_id": "EV-1", "source_id": "SRC-1", "chunk_id": "CH-1", "hash": "sha256:1"}],
                )

        harness = RecordingHarness()
        result = OrchestratorGraph(harness).run(self.work_order, str(self.storage.project_path))
        self.assertEqual(result["status"], "complete")
        self.assertEqual([(phase, agent_id) for phase, agent_id, _ in harness.calls], list(FLOW))
        self.assertEqual([cycle for _, _, cycle in harness.calls], [f"CYC-{idx:03d}" for idx in range(1, len(FLOW) + 1)])

    def test_orchestrator_retries_when_qa_fails(self) -> None:
        class FakeHarness:
            def __init__(self) -> None:
                self.calls = 0

            def run_agent(self, agent_id, state):
                self.calls += 1
                if self.calls == 1:
                    return make_agent_output(
                        agent_id=agent_id,
                        task_id=state["task_id"],
                        status="error",
                        summary="schema reparable",
                        artifacts=[],
                        evidence=[{"evidence_id": "EV-1", "source_id": "SRC-1", "chunk_id": "CH-1", "hash": "sha256:1"}],
                        issues=["schema_recoverable"],
                        next_action="retry",
                    )
                return make_agent_output(
                    agent_id=agent_id,
                    task_id=state["task_id"],
                    status="complete",
                    summary="ok",
                    artifacts=[],
                    evidence=[{"evidence_id": "EV-1", "source_id": "SRC-1", "chunk_id": "CH-1", "hash": "sha256:1"}],
                )

        fake = FakeHarness()
        result = OrchestratorGraph(fake)._run_with_retries("agent.qa", self.state("analyze"), max_retries=2)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(fake.calls, 2)

    def test_evidence_validator_rejects_missing_refs(self) -> None:
        output = make_agent_output(
            agent_id="agent.qa",
            task_id="TASK-TEST",
            status="complete",
            summary="sin evidencia",
            artifacts=[],
            evidence=[],
        )
        report = ValidatorChain(self.storage).validate_all(output, self.state("validate"))
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["next_action"], "not_answerable")

    def test_schema_validator_rejects_invalid_json(self) -> None:
        report = ValidatorChain(self.storage).validate_all({"status": "complete"}, self.state("validate"))
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["next_action"], "error")

    def test_memory_filter_excludes_deprecated_memory(self) -> None:
        records = [
            {"scope": "project", "approval_status": "approved", "taint_status": "clean", "ttl": "P30D", "content": "ok"},
            {"scope": "project", "approval_status": "proposed", "taint_status": "clean", "ttl": "P30D", "content": "no"},
            {"scope": "project", "approval_status": "approved", "taint_status": "tainted", "ttl": "P30D", "content": "no"},
            {"scope": "project", "approval_status": "approved", "taint_status": "clean", "ttl": "expired", "content": "no"},
        ]
        filtered = MemoryGate(self.storage).filter_records(records, agent_id="agent.spec", scopes=("project",))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["content"], "ok")

    def test_project_learning_handoff_and_memory_ledgers_are_isolated(self) -> None:
        self.assertTrue((self.storage.project_path / "Aprendizaje.md").exists())
        self.assertTrue((self.storage.project_path / "HANDOFF.md").exists())
        self.assertIn("contexto toxico", (self.storage.project_path / "HANDOFF.md").read_text(encoding="utf-8"))
        ledgers = self.storage.memory_ledger_paths()
        self.assertNotEqual(ledgers["factory"], ledgers["project"])
        self.storage.write_json(
            ledgers["factory"],
            [
                {
                    "memory_id": "MEM-FACTORY",
                    "scope": "factory",
                    "approval_status": "approved",
                    "taint_status": "clean",
                    "ttl": "P30D",
                    "content": "factory-only",
                }
            ],
        )
        self.storage.write_json(
            ledgers["project"],
            [
                {
                    "memory_id": "MEM-PROJECT",
                    "scope": "project",
                    "approval_status": "approved",
                    "taint_status": "clean",
                    "ttl": "P30D",
                    "content": "project-only",
                },
                {
                    "memory_id": "MEM-TAINTED",
                    "scope": "project",
                    "approval_status": "approved",
                    "taint_status": "tainted",
                    "ttl": "P30D",
                    "content": "toxic",
                },
            ],
        )
        memory = MemoryGate(self.storage)
        project_pack = memory.read_filtered("agent.spec", ("project",))
        factory_pack = memory.read_filtered("agent.spec", ("factory",))
        self.assertEqual([record["content"] for record in project_pack["records"]], ["project-only"])
        self.assertEqual([record["content"] for record in factory_pack["records"]], ["factory-only"])
        self.assertEqual(project_pack["records"][0]["memory_ledger_scope"], "project")
        self.assertEqual(factory_pack["records"][0]["memory_ledger_scope"], "factory")

    def test_cost_metrics_are_logged(self) -> None:
        harness = HarnessRunner(self.storage)
        result = harness.run_agent("agent.spec", self.state("constitution"))
        self.assertEqual(result["status"], "complete")
        self.assertIn("usage_estimate", result)
        self.assertGreaterEqual(result["usage_estimate"]["input_tokens"], 1)
        self.assertGreaterEqual(result["usage_estimate"]["output_tokens"], 1)
        ledger = self.storage.read_json("billing-ledger.json")
        self.assertGreaterEqual(ledger["totals"]["input_tokens"], 1)
        self.assertIn("tool_calls", ledger["totals"])
        self.assertIn("pricing_version", ledger)
        self.assertIn("billable_input_tokens", ledger["totals"])

    def test_real_token_billing_uses_official_rates(self) -> None:
        usage = normalize_usage(
            {
                "input_tokens": 1_000_000,
                "input_tokens_details": {"cached_tokens": 100_000},
                "output_tokens": 500_000,
                "output_tokens_details": {"reasoning_tokens": 25_000},
                "total_tokens": 1_500_000,
            }
        )
        priced = PricingCatalog().calculate(model="gpt-5.4", usage=usage)
        self.assertEqual(priced["status"], "complete")
        self.assertEqual(priced["usage"]["billable_input_tokens"], 900_000)
        self.assertEqual(priced["usage"]["visible_output_tokens"], 475_000)
        self.assertEqual(priced["cost_breakdown_usd"]["total"], "9.775000")

    def test_unknown_model_billing_is_not_answerable(self) -> None:
        usage = normalize_usage({"input_tokens": 10, "output_tokens": 10})
        priced = PricingCatalog().calculate(model="modelo-no-oficial", usage=usage)
        self.assertEqual(priced["status"], "not_answerable")
        self.assertEqual(priced["reason"], "missing_official_rate_for_model_or_tier")

    def test_orchestrator_passes_real_api_usage_to_billing(self) -> None:
        work_order = {
            **self.work_order,
            "billing": {"model": "gpt-5.4", "service_tier": "standard", "context": "short"},
            "api_usage_by_phase": {
                "constitution:agent.spec": {
                    "input_tokens": 1_000_000,
                    "input_tokens_details": {"cached_tokens": 100_000},
                    "output_tokens": 500_000,
                    "output_tokens_details": {"reasoning_tokens": 25_000},
                    "total_tokens": 1_500_000,
                }
            },
        }
        OrchestratorGraph(HarnessRunner(self.storage), max_steps=1).run(work_order, str(self.storage.project_path))
        first = self.storage.read_json("billing-ledger.json")["phases"][0]
        self.assertTrue(first["billing_is_real_api_usage"])
        self.assertEqual(first["model"], "gpt-5.4")
        self.assertEqual(first["estimated_cost"], "9.775000")

    def test_frontend_design_tokens_validate(self) -> None:
        self.assertEqual(validate_design_tokens()["status"], "pass")
        self.assertEqual(audit_contrast()["status"], "pass")

    def test_frontend_agents_generate_artifacts(self) -> None:
        harness = HarnessRunner(self.storage)
        result = harness.run_agent("agent.frontend_design_system", self.state("design_system"))
        self.assertEqual(result["status"], "complete")
        self.assertTrue(self.storage.path("DESIGN_SYSTEM.md").exists())
        self.assertTrue(self.storage.path("frontend-quality-contract.json").exists())
        ux = harness.run_agent("agent.ux_accessibility", self.state("ux_accessibility"))
        self.assertEqual(ux["status"], "complete")
        self.assertTrue(self.storage.path("ux-accessibility-report.json").exists())
        self.assertTrue(self.storage.path("responsive-matrix.json").exists())

    def test_permanent_practices_hash_recorded(self) -> None:
        result = HarnessRunner(self.storage).run_agent("agent.frontend_design_system", self.state("design_system"))
        self.assertEqual(result["status"], "complete")
        text = self.storage.read_text("PRACTICAS_PERMANENTES.md")
        self.assertIn(BEST_PRACTICES_HASH, text)

    def test_repeated_runs_are_stable(self) -> None:
        first = OrchestratorGraph(HarnessRunner(self.storage)).run(self.work_order, str(self.storage.project_path))
        self.storage.reset_run_outputs()
        second = OrchestratorGraph(HarnessRunner(self.storage)).run(self.work_order, str(self.storage.project_path))
        self.assertEqual(first["status"], second["status"])
        self.assertEqual(first["passed_gates"], second["passed_gates"])
        self.assertEqual(first["phase_count"], second["phase_count"])

    def test_policy_denies_unallowlisted_tool(self) -> None:
        agent = AgentRegistry().get("agent.spec")
        tool = ToolRegistry().get("tool.index.query")
        with self.assertRaises(PolicyDecision):
            PolicyEngine().evaluate_tool(agent, tool, self.state())

    def test_context_pack_uses_chunks_not_full_docs(self) -> None:
        long_text = "# Long\n" + ("evidencia cache index memoria gates " * 300)
        self.storage.write_text("long-design.md", long_text)
        harness = HarnessRunner(self.storage)
        result = harness.run_agent("agent.context_rag", self.state("context"))
        self.assertEqual(result["status"], "complete")
        pack = self.storage.read_json("context-pack.json")
        self.assertLessEqual(max(len(chunk["content"]) for chunk in pack["chunks"]), 1400)


if __name__ == "__main__":
    unittest.main()
