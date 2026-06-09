# Traceability Matrix

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
