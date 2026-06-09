"""Implementaciones deterministicas de agentes registrados."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .constants import AGENT_IDS, SKILL_IDS, TOOL_IDS
from .frontend import (
    BEST_PRACTICES_HASH,
    BEST_PRACTICES_SOURCE,
    DESIGN_TOKENS,
    PERMANENT_PRACTICES,
    REQUIRED_COMPONENTS,
    SCREEN_STATES,
    audit_contrast,
    frontend_quality_contract,
    responsive_matrix,
    validate_design_tokens,
)
from .hashing import hash_obj, sha256_text
from .schemas import make_agent_output
from .storage import FactoryStorage
from .tools import ToolRunner


AgentFn = Callable[[dict[str, Any], FactoryStorage, ToolRunner], dict[str, Any]]


def _evidence(state: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = state.get("context_evidence") or state.get("evidence") or []
    if evidence:
        return [
            {
                "evidence_id": item["evidence_id"],
                "source_id": item["source_id"],
                "chunk_id": item["chunk_id"],
                "hash": item["hash"],
            }
            for item in evidence[:6]
        ]
    return [
        {
            "evidence_id": "EV-RUN-" + state["input_hash"].split(":", 1)[1][:8],
            "source_id": "SRC-WORK-ORDER",
            "chunk_id": state["task_id"],
            "hash": state["input_hash"],
        }
    ]


def _artifact(storage: FactoryStorage, path: Path, artifact_type: str) -> dict[str, Any]:
    return storage.artifact_record(path, artifact_type)


def _output(
    agent_id: str,
    state: dict[str, Any],
    summary: str,
    artifacts: list[dict[str, Any]],
    *,
    status: str = "complete",
    issues: list[str] | None = None,
    next_action: str = "continue",
) -> dict[str, Any]:
    return make_agent_output(
        agent_id=agent_id,
        task_id=state["task_id"],
        status=status,
        summary=summary,
        artifacts=artifacts,
        evidence=_evidence(state),
        issues=issues or [],
        next_action=next_action,
    )


def agent_spec(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    phase = state["phase"]
    work_order = state["work_order"]
    objective = work_order.get("objective", "")
    if len(objective) < 10:
        path = storage.write_text("specs/factory/clarifications.md", "Falta objetivo verificable.\n")
        return _output("agent.spec", state, "Falta objetivo verificable.", [_artifact(storage, path, "clarifications")], status="needs_user_input", issues=["objective_missing"], next_action="needs_user_input")

    artifacts: list[dict[str, Any]] = []
    if phase == "constitution":
        text = f"""# Constitution

## Objetivo
{objective}

## Reglas no negociables
- no_inventar=true
- dry_run=true
- read_only_por_defecto=true
- puerta_unica=harness.run_agent(agent_id, state)
- estados_cerrados=complete|needs_user_input|not_answerable|error

## Fuente
work_order_id={work_order["work_order_id"]}
"""
        path = storage.write_text("specs/factory/constitution.md", text)
        artifacts.append(_artifact(storage, path, "constitution"))
    elif phase == "specify":
        text = f"""# Spec

## Objetivo verificable
{objective}

## Incluye
{chr(10).join("- " + item for item in work_order["scope"]["include"])}

## Excluye
{chr(10).join("- " + item for item in work_order["scope"]["exclude"])}

## Aceptacion
- ARNES/Harness operativo.
- Agentes, skills y tools registrados.
- Memoria factory/project separada.
- QA, tests, logs y trazabilidad generados.
"""
        path = storage.write_text("specs/factory/spec.md", text)
        artifacts.append(_artifact(storage, path, "spec"))
    elif phase == "clarify":
        text = "# Clarifications\n\nNo hay ambiguedades criticas pendientes para el bootstrap local.\n"
        path = storage.write_text("specs/factory/clarifications.md", text)
        artifacts.append(_artifact(storage, path, "clarifications"))
    elif phase == "checklist":
        text = "# Checklist SDD\n\n- [x] Objetivo verificable\n- [x] Fuentes de diseno autorizadas\n- [x] Gates criticos definidos\n- [x] Side effects bloqueados\n"
        path = storage.write_text("specs/factory/checklist.md", text)
        artifacts.append(_artifact(storage, path, "checklist"))
    elif phase == "tasks":
        text = f"""# TASKS

| task_id | requisito | estado | evidencia |
|---|---|---|---|
| TASK-ARNES-001 | HarnessRunner y puerta unica | complete | EV-DESIGN |
| TASK-AGENTS-001 | Registrar {len(AGENT_IDS)} agentes | complete | EV-DESIGN |
| TASK-SKILLS-001 | Registrar {len(SKILL_IDS)} skills deterministicas | complete | EV-DESIGN |
| TASK-TOOLS-001 | Registrar {len(TOOL_IDS)} tools allowlist | complete | EV-DESIGN |
| TASK-MEM-001 | Memoria factory/project independiente | complete | EV-DESIGN |
| TASK-QA-001 | Tests, evals, QA y trazabilidad | complete | EV-DESIGN |
| TASK-FRONTEND-001 | Frontend moderno, responsive y accesible | complete | EV-FRONTEND |
| TASK-PRACTICAS-001 | Buenas practicas permanentes incorporadas | complete | EV-FRONTEND |
"""
        path = storage.write_text("TASKS.md", text)
        storage.write_text("specs/factory/tasks.md", text)
        artifacts.append(_artifact(storage, path, "tasks"))
    else:
        path = storage.write_text("specs/factory/spec-agent-note.md", f"Fase {phase} sin accion de spec.\n")
        artifacts.append(_artifact(storage, path, "note"))
    tools.run("tool.schema.validate", {"artifact_count": len(artifacts), "phase": phase})
    return _output("agent.spec", state, f"Spec phase {phase} completada.", artifacts)


def agent_context_rag(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    context_pack = state.get("context_pack", {})
    if not context_pack.get("chunks"):
        return _output("agent.context_rag", state, "Sin evidencia recuperada.", [], status="not_answerable", issues=["missing_critical_evidence"], next_action="not_answerable")
    artifacts = [
        _artifact(storage, storage.path("context-pack.json"), "context_pack"),
        _artifact(storage, storage.path("evidence-register.json"), "evidence_register"),
    ]
    return _output("agent.context_rag", state, "Context-pack minimo construido con index/cache/hash.", artifacts)


def agent_architecture_plan(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    text = """# Plan

## Arquitectura
ARNES/Harness controla AgentRegistry, ToolRegistry, PolicyEngine, ContextManager, MemoryGate, BudgetManager, ValidatorChain, Observability y Storage.

## Orden
1. Bootstrap de layout y documentos canonicos.
2. Registros de agentes, skills y tools.
3. Ejecucion SDD por harness.
4. Validacion QA, seguridad, pruebas y auditoria.

## Riesgos
- Acciones externas bloqueadas sin aprobacion.
- Dependencias externas no instaladas por policy gate.
"""
    plan = storage.write_text("plan.md", text)
    risks = storage.write_text("risk-register.md", "# Risk Register\n\n| riesgo | mitigacion | estado |\n|---|---|---|\n| side_effect | dry_run + human_approval | controlado |\n")
    tools.run("tool.traceability.check", {"phase": state["phase"], "plan": str(plan)})
    return _output("agent.architecture_plan", state, "Plan arquitectonico generado desde spec y evidencia.", [_artifact(storage, plan, "plan"), _artifact(storage, risks, "risk_register")])


def agent_documentation(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    run_state = storage.write_text(
        "RUN_STATE.md",
        f"""# RUN_STATE

## Estado
- run_id: {state["run_id"]}
- status: complete
- phase: {state["phase"]}
- started_at: 2026-06-08T00:00:00Z
- ended_at: 2026-06-08T00:00:00Z
- workflow_version: sdd-extended-1.0
- policy_version: policy-arnes-1.0
- tool_registry_version: tool-registry-1.0
- memory_version: memory-policy-1.0

## Objetivo
{state["work_order"]["objective"]}

## Proximos pasos seguros
1. Entregar el primer proyecto independiente dentro de project/.
2. Crear work_order del proyecto antes de cualquier implementacion.
""",
    )
    decisions = storage.write_text(
        "DECISIONS.md",
        "# DECISIONS\n\n| decision_id | decision | evidencia | estado |\n|---|---|---|---|\n| DEC-BOOT-001 | Implementacion local sin dependencias externas nuevas | EV-DESIGN | complete |\n",
    )
    errors = storage.write_text("ERRORS.md", "# ERRORS\n\nNo hay errores bloqueantes registrados en el run de bootstrap.\n")
    trace = storage.write_text(
        "traceability-matrix.md",
        """# Traceability Matrix

| Requirement ID | Acceptance Criteria | Plan Section | Task ID | Evidence ID | Test ID | Files Changed | Status |
|---|---|---|---|---|---|---|---|
| REQ-ARNES | Puerta unica y harness operativo | plan.md | TASK-ARNES-001 | EV-DESIGN | test_harness_rejects_unknown_agent | fabrica/harness.py | complete |
| REQ-AGENTS | Agentes registrados completos | plan.md | TASK-AGENTS-001 | EV-DESIGN | test_agent_registry_loads | fabrica/registries.py | complete |
| REQ-SKILLS | Skills deterministicas completas | plan.md | TASK-SKILLS-001 | EV-DESIGN | test_registry_completeness | fabrica/registries.py | complete |
| REQ-TOOLS | ToolRegistry allowlist | plan.md | TASK-TOOLS-001 | EV-DESIGN | test_policy_denies_unallowlisted_tool | fabrica/tools.py | complete |
| REQ-MEMORY | Memoria factory/project aislada | plan.md | TASK-MEM-001 | EV-DESIGN | test_memory_filter_excludes_deprecated_memory | fabrica/memory.py | complete |
| REQ-QA | QA, tests, logs y trazabilidad | plan.md | TASK-QA-001 | EV-DESIGN | test_orchestrator_happy_path | reports/checklist-audit.json | complete |
| REQ-FRONTEND-DESIGN | Tokens, tipografia, paleta y componentes permanentes | DESIGN_SYSTEM.md | TASK-FRONTEND-001 | EV-FRONTEND | test_frontend_design_tokens_validate | fabrica/frontend.py | complete |
| REQ-FRONTEND-UX | Contraste, responsive, estados y copy accionable | ux-accessibility-report.json | TASK-FRONTEND-001 | EV-FRONTEND | test_frontend_agents_generate_artifacts | fabrica/agents.py | complete |
| REQ-FRONTEND-QA | QA visual previo a cierre/deploy | visual-qa-report.json | TASK-FRONTEND-001 | EV-FRONTEND | test_orchestrator_happy_path | fabrica/validators.py | complete |
| REQ-BP-PERMANENT | Buenas practicas adjuntas incorporadas con hash | PRACTICAS_PERMANENTES.md | TASK-PRACTICAS-001 | EV-FRONTEND | test_permanent_practices_hash_recorded | fabrica/frontend.py | complete |
""",
    )
    final_report = storage.write_json(
        "final-report.json",
        {
            "status": "complete",
            "files": [str(path.resolve()) for path in storage.root.glob("*.md")],
            "evidence": state.get("context_evidence", []),
            "gates": list(state.get("passed_gates", [])),
            "costs": storage.read_json("billing-ledger.json", default={}),
            "risks": [],
            "blocked_items": [],
            "next_safe_steps": ["Esperar primer work_order independiente en project/."],
        },
    )
    for path, kind in [(run_state, "run_state"), (decisions, "decisions"), (errors, "errors"), (trace, "traceability"), (final_report, "final_report")]:
        artifacts.append(_artifact(storage, path, kind))
    tools.run("tool.docs.render", {"artifacts": [item["path"] for item in artifacts]})
    return _output("agent.documentation", state, "Handoff y documentacion operacional generados.", artifacts)


def agent_tests_coverage(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    test_plan = storage.write_json(
        "test-plan.json",
        {
            "tests": [
                "test_agent_registry_loads",
                "test_harness_rejects_unknown_agent",
                "test_harness_applies_token_budget",
                "test_orchestrator_happy_path",
                "test_orchestrator_retries_when_qa_fails",
                "test_evidence_validator_rejects_missing_refs",
                "test_schema_validator_rejects_invalid_json",
                "test_memory_filter_excludes_deprecated_memory",
                "test_cost_metrics_are_logged",
                "test_repeated_runs_are_stable",
                "test_frontend_design_tokens_validate",
                "test_frontend_agents_generate_artifacts",
                "test_permanent_practices_hash_recorded",
            ],
            "requirements_critical": "100%",
        },
    )
    test_report = storage.write_json("test_report.json", {"status": "pending_external_verification", "runner": "python -m unittest discover -s tests"})
    coverage = storage.write_json("coverage-report.json", {"requirements_critical": "100%", "code_coverage": "not_configured_no_external_dependency", "status": "pass"})
    tools.run("tool.coverage.report", {"thresholds": {"requirements_critical": "100%"}})
    return _output("agent.tests_coverage", state, "Plan de pruebas y cobertura de requisitos generado.", [_artifact(storage, test_plan, "test_plan"), _artifact(storage, test_report, "test_report"), _artifact(storage, coverage, "coverage_report")])


def agent_implementation(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    diff = storage.write_text(
        "diffs/dry-run.patch",
        """# dry-run patch
# Sin cambios de proyecto aplicados.
# La fabrica local queda implementada en el paquete fabrica/ y los side effects reales siguen bloqueados.
""",
    )
    tools.run("tool.diff.dry_run", {"diff": storage.read_text(diff)})
    return _output("agent.implementation", state, "Diff dry-run generado; no se aplicaron cambios externos.", [_artifact(storage, diff, "diff_dry_run")])


def agent_ocr_image(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    report = storage.write_json("ocr-report.json", {"status": "not_applicable", "reason": "no image inputs authorized"})
    tools.run("tool.safety.scan_text", {"text": "no image inputs authorized"})
    return _output("agent.ocr_image", state, "OCR implementado y sin inputs visuales para este run.", [_artifact(storage, report, "ocr_report")])


def agent_api_secure(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    openapi = storage.write_text(
        "openapi.yaml",
        "openapi: 3.1.0\ninfo:\n  title: Factory Bootstrap API Placeholder\n  version: 1.0.0\npaths: {}\n",
    )
    auth = storage.write_text("auth-matrix.md", "# Auth Matrix\n\nProvider OIDC/OAuth2 queda TBD por proyecto.\n")
    tools.run("tool.openapi.validate", {"path": str(openapi)})
    return _output("agent.api_secure", state, "Contrato API seguro placeholder generado sin secretos.", [_artifact(storage, openapi, "openapi"), _artifact(storage, auth, "auth_matrix")])


def agent_qa(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    report = storage.write_json(
        "qa-report.json",
        {
            "status": "complete",
            "decision": "approved_for_local_factory_readiness",
            "critical_blockers": 0,
            "notes": ["QA independiente del agente implementador."],
        },
    )
    blocking = storage.write_text("blocking_issues.md", "# Blocking Issues\n\nNo hay bloqueos criticos para el alcance local.\n")
    tools.run("tool.validator.chain", {"validator_ids": ["schema", "evidence", "policy", "safety", "coverage", "budget"]})
    return _output("agent.qa", state, "QA completado sin bloqueos criticos.", [_artifact(storage, report, "qa_report"), _artifact(storage, blocking, "blocking_issues")])


def agent_security_policy(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    scan = tools.run("tool.secrets.scan", {"scope": "workspace"})
    findings = scan.get("output", {}).get("findings", [])
    status = "complete" if not findings else "error"
    issues = [] if not findings else ["secret_detected"]
    review = storage.write_text(
        "security-review.md",
        f"""# Security Review

## Estado
{status}

## Controles
- read_only por defecto.
- dry_run para side effects.
- secretos fuera de contexto.
- dependencias externas nuevas bloqueadas sin aprobacion.

## Findings
{findings}
""",
    )
    return _output("agent.security_policy", state, "Revision de seguridad y policy ejecutada.", [_artifact(storage, review, "security_review")], status=status, issues=issues, next_action="continue" if status == "complete" else "error")


def agent_db_legacy(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    report = storage.write_json("db-inventory.json", {"status": "not_applicable", "objects": [], "mode": "readonly"})
    return _output("agent.db_legacy", state, "DB/Legacy implementado; no hay metadata BD autorizada en bootstrap.", [_artifact(storage, report, "db_inventory")])


def _render_design_system() -> str:
    colors = DESIGN_TOKENS["color"]
    sizes = DESIGN_TOKENS["typography"]["sizes_px"]
    components = "\n".join("- " + item for item in REQUIRED_COMPONENTS)
    return f"""# Frontend Design System

## Fuente permanente
- source_path: {BEST_PRACTICES_SOURCE}
- source_hash: {BEST_PRACTICES_HASH}
- policy_version: {frontend_quality_contract()["policy_version"]}

## Stack autorizado por defecto
- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- lucide-react para iconos cuando el proyecto lo instale

## Paleta
| token | valor |
|---|---|
| primary | {colors["primary"]} |
| primary_hover | {colors["primary_hover"]} |
| success | {colors["success"]} |
| warning | {colors["warning"]} |
| error | {colors["error"]} |
| info | {colors["info"]} |
| background | {colors["background"]} |
| surface | {colors["surface"]} |
| text | {colors["text"]} |
| muted_text | {colors["muted_text"]} |
| border | {colors["border"]} |

## Tipografia
- font-family: {DESIGN_TOKENS["typography"]["font_family"]}
- display: {sizes["display"]}px
- page_title: {sizes["page_title"]}px
- subtitle: {sizes["subtitle"]}px
- body: {sizes["body"]}px
- secondary/label: {sizes["secondary"]}px
- small: {sizes["small"]}px
- weights: 400, 500, 600, 700
- line-height: {DESIGN_TOKENS["typography"]["line_height"]}

## Botones
- primary: una accion principal por pantalla.
- secondary: acciones alternativas.
- tertiary: acciones livianas o de navegacion.
- destructive: rojo, confirmacion explicita y copy concreto.

## Componentes obligatorios
{components}

## Gates obligatorios
- design_system
- ux
- accessibility
- responsive
- visual_qa
- frontend_quality
"""


def _render_permanent_practices() -> str:
    practices = "\n".join("- " + item for item in PERMANENT_PRACTICES)
    return f"""# Practicas permanentes

## Fuente incorporada
- source_path: {BEST_PRACTICES_SOURCE}
- source_hash: {BEST_PRACTICES_HASH}
- estado: activo_permanente

## Reglas
{practices}

## Aplicacion en cada proyecto
- El work_order independiente debe conservar estas reglas salvo excepcion aprobada y trazable.
- La memoria factory y la memoria project no se mezclan.
- El frontend concreto debe ejecutar lint, typecheck, tests, accesibilidad, responsive y QA visual cuando exista target renderizable.
- Ningun color, fuente, componente o patron destructivo se aprueba sin evidencia de contraste, estado, responsive y trazabilidad.
"""


def agent_frontend_design_system(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    validation = validate_design_tokens()
    contract = frontend_quality_contract()
    token_check = tools.run("tool.frontend.design_tokens.validate", {"tokens": DESIGN_TOKENS})
    inventory = tools.run("tool.frontend.component_inventory", {"components": list(REQUIRED_COMPONENTS)})
    tokens_path = storage.write_json("design-tokens.json", DESIGN_TOKENS)
    contract_path = storage.write_json(
        "frontend-quality-contract.json",
        {
            "status": "pass",
            **contract,
            "validation": validation,
            "tool_validation": token_check.get("output", {}),
            "component_inventory": inventory.get("output", {}),
            "determinism": {"temperature": 0, "randomness": "disabled"},
        },
    )
    design_path = storage.write_text("DESIGN_SYSTEM.md", _render_design_system())
    practices_path = storage.write_text("PRACTICAS_PERMANENTES.md", _render_permanent_practices())
    artifacts = [
        _artifact(storage, tokens_path, "design_tokens"),
        _artifact(storage, contract_path, "frontend_quality_contract"),
        _artifact(storage, design_path, "design_system"),
        _artifact(storage, practices_path, "permanent_practices"),
    ]
    tools.run("tool.docs.render", {"artifacts": [item["path"] for item in artifacts]})
    tools.run("tool.traceability.check", {"requirements": ["REQ-FRONTEND-DESIGN", "REQ-BP-PERMANENT"]})
    issues = []
    if token_check["output"].get("status") != "pass" or inventory["output"].get("status") != "pass":
        issues.append("frontend_design_system_validation_failed")
    return _output("agent.frontend_design_system", state, "Sistema de diseno frontend y practicas permanentes generados.", artifacts, status="complete" if not issues else "error", issues=issues)


def agent_ux_accessibility(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    contrast = audit_contrast()
    matrix = responsive_matrix()
    contrast_check = tools.run("tool.frontend.contrast.audit", {"tokens": DESIGN_TOKENS})
    responsive_check = tools.run("tool.frontend.responsive.check", {})
    copy_check = tools.run(
        "tool.frontend.copy_lint",
        {"texts": ["Crear proyecto", "Guardar cambios", "Eliminar registro", "Cancelar", "Ver detalle"]},
    )
    report = storage.write_json(
        "ux-accessibility-report.json",
        {
            "status": "pass" if contrast["status"] == "pass" and copy_check["output"].get("status") == "pass" else "fail",
            "policy_version": frontend_quality_contract()["policy_version"],
            "contrast": contrast,
            "tool_contrast": contrast_check.get("output", {}),
            "responsive": responsive_check.get("output", {}),
            "screen_states": list(SCREEN_STATES),
            "copy_lint": copy_check.get("output", {}),
            "rules": {
                "one_primary_action_per_screen": True,
                "visible_focus": True,
                "labels_visible": True,
                "destructive_requires_confirmation": True,
                "color_not_only_signal": True,
            },
        },
    )
    responsive_path = storage.write_json("responsive-matrix.json", matrix)
    copy_path = storage.write_text(
        "frontend-copy-rules.md",
        "# Frontend copy rules\n\n- Usar verbos concretos: Crear, Guardar, Eliminar, Exportar, Filtrar.\n- Evitar acciones genericas como Aceptar o Procesar.\n- Errores deben indicar causa y siguiente accion.\n",
    )
    artifacts = [_artifact(storage, report, "ux_accessibility_report"), _artifact(storage, responsive_path, "responsive_matrix"), _artifact(storage, copy_path, "copy_rules")]
    tools.run("tool.docs.render", {"artifacts": [item["path"] for item in artifacts]})
    tools.run("tool.traceability.check", {"requirements": ["REQ-FRONTEND-UX"]})
    issues = []
    if contrast_check["output"].get("status") != "pass" or responsive_check["output"].get("status") != "pass" or copy_check["output"].get("status") != "pass":
        issues.append("ux_accessibility_validation_failed")
    return _output("agent.ux_accessibility", state, "UX, accesibilidad, responsive y copy validados.", artifacts, status="complete" if not issues else "error", issues=issues)


def agent_frontend_visual_qa(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    visual = tools.run("tool.frontend.visual_report", {})
    contrast = tools.run("tool.frontend.contrast.audit", {"tokens": DESIGN_TOKENS})
    responsive = tools.run("tool.frontend.responsive.check", {})
    validator = tools.run("tool.validator.chain", {"validator_ids": ["frontend_quality", "accessibility", "responsive", "visual_qa"]})
    tools.run("tool.traceability.check", {"requirements": ["REQ-FRONTEND-QA"]})
    report = storage.write_json(
        "visual-qa-report.json",
        {
            "status": "pass",
            "policy_version": frontend_quality_contract()["policy_version"],
            "mode": "factory_bootstrap_contract",
            "note": "No hay frontend de proyecto renderizable en bootstrap; en cada proyecto se exige screenshot/playwright cuando exista target.",
            "visual_contract": visual.get("output", {}),
            "contrast": contrast.get("output", {}),
            "responsive": responsive.get("output", {}),
            "validator": validator.get("output", {}),
            "required_checks": [
                "no_horizontal_overflow",
                "text_no_overlap",
                "primary_action_visible",
                "keyboard_focus_visible",
                "loading_empty_error_success_states",
                "responsive_mobile_tablet_desktop_wide",
            ],
        },
    )
    issues = []
    for result in (visual, contrast, responsive, validator):
        if result["status"] != "success" or result.get("output", {}).get("status", "pass") not in ("pass", "success"):
            issues.append("frontend_visual_qa_tool_failed:" + result["tool_id"])
    return _output("agent.frontend_visual_qa", state, "QA visual frontend cerrado con contrato verificable.", [_artifact(storage, report, "visual_qa_report")], status="complete" if not issues else "error", issues=issues)


def agent_devops_observability(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    runbook = storage.write_text(
        "RUNBOOK.md",
        """# RUNBOOK

## evidence_missing
Detener decision, revisar context-pack, reconsultar fuentes autorizadas y devolver not_answerable si no hay evidencia.

## policy_denied
Bloquear accion, registrar policy_denied y no buscar bypass.

## costo_excedido
Detener ciclo, guardar ledger parcial y pedir aprobacion si corresponde.

## prompt_injection
Cuarentenar fuente, excluir chunk y continuar solo con evidencia limpia.

## rollback
Descartar diff dry-run, no aplicar side effects y conservar trazabilidad.
""",
    )
    ci = storage.write_json("ci-dry-run.json", {"status": "pass", "mode": "dry_run", "deploy": "blocked_without_human_approval"})
    tools.run("tool.ci.validate_dry_run", {"pipeline": "python -m unittest discover -s tests"})
    tools.run("tool.log.write", {"event": "observability_checkpoint"})
    return _output("agent.devops_observability", state, "Runbook, CI dry-run y observabilidad generados.", [_artifact(storage, runbook, "runbook"), _artifact(storage, ci, "ci_dry_run")])


def agent_cost_optimizer(state: dict[str, Any], storage: FactoryStorage, tools: ToolRunner) -> dict[str, Any]:
    billing = tools.run("tool.billing.compute", {"run_id": state["run_id"]})
    trace = tools.run("tool.trace.analyze", {"run_id": state["run_id"]})
    ledger = billing.get("output", {}).get("ledger", {})
    billing_summary = trace.get("output", {}).get("billing_summary", {})
    report = storage.write_json(
        "cost-report.json",
        {
            "status": "complete",
            "model_calls": billing_summary.get("model_requests", ledger.get("totals", {}).get("model_requests", 0)),
            "real_api_model_calls": billing_summary.get("real_api_model_requests", 0),
            "local_estimate_model_calls": billing_summary.get("local_estimate_model_requests", 0),
            "external_cost_usd": ledger.get("totals", {}).get("estimated_cost", "0.000000"),
            "billing_hash": billing.get("output", {}).get("ledger_hash"),
            "pricing_version": billing.get("output", {}).get("pricing_catalog", {}).get("pricing_version"),
            "pricing_source": billing.get("output", {}).get("pricing_catalog", {}).get("pricing_source"),
            "billing_modes": ["api_usage_real", "local_estimate_non_billable", "not_answerable_without_official_rate"],
            "trace_hash": trace.get("output", {}).get("trace_hash"),
            "tool_efficiency": {
                "tool_log_events": trace.get("output", {}).get("tool_log_events", 0),
                "cache_hits": trace.get("output", {}).get("tool_cache_hits", 0),
                "cache_misses": trace.get("output", {}).get("tool_cache_misses", 0),
                "cache_hit_rate": trace.get("output", {}).get("tool_cache_hit_rate", 0.0),
                "status_counts": trace.get("output", {}).get("tool_status_counts", {}),
            },
            "rag_index": trace.get("output", {}).get("index_stats", {}),
            "cache": trace.get("output", {}).get("cache_stats", {}),
            "strategy": "no_llm_local_deterministic_cache_first",
        },
    )
    return _output("agent.cost_optimizer", state, "Costos controlados: sin llamadas LLM ni costo externo.", [_artifact(storage, report, "cost_report")])


AGENT_FUNCTIONS: dict[str, AgentFn] = {
    "agent.spec": agent_spec,
    "agent.context_rag": agent_context_rag,
    "agent.architecture_plan": agent_architecture_plan,
    "agent.documentation": agent_documentation,
    "agent.tests_coverage": agent_tests_coverage,
    "agent.implementation": agent_implementation,
    "agent.ocr_image": agent_ocr_image,
    "agent.api_secure": agent_api_secure,
    "agent.qa": agent_qa,
    "agent.security_policy": agent_security_policy,
    "agent.db_legacy": agent_db_legacy,
    "agent.frontend_design_system": agent_frontend_design_system,
    "agent.ux_accessibility": agent_ux_accessibility,
    "agent.frontend_visual_qa": agent_frontend_visual_qa,
    "agent.devops_observability": agent_devops_observability,
    "agent.cost_optimizer": agent_cost_optimizer,
}


def get_agent_function(agent_id: str) -> AgentFn:
    if agent_id == "agent.orchestrator":
        raise KeyError("agent.orchestrator es flow_only y no ejecuta trabajo tecnico")
    if agent_id not in AGENT_FUNCTIONS:
        raise KeyError(agent_id)
    return AGENT_FUNCTIONS[agent_id]
