# Arquitectura, Stack y Flujos SDD

## Metadatos de generación y versionado

| campo | valor |
|---|---|
| factory_version | `0.1.0` |
| schema_version | `arnes-sdd-1.0` |
| workflow_version | `sdd-extended-1.0` |
| policy_version | `policy-arnes-1.0` |
| tools_version | `tool-registry-draft-0.1.0` |
| memory_version | `memory-policy-1.0` |
| RAG index_version | `TBD` |
| eval_set_version | `eval-set-arnes-1.0` |
| model/snapshot | `gpt-5.5-or-fixed-snapshot:TBD` |
| prompt_hash | `sha256:7d5c9cc6116b4709479935ae7db38de6455605d0338d2ef56aa7edeb3a0ef29d` |
| fecha_generación | `2026-06-08` |
| modo | `diseño_factory`, `read-only`, `dry-run`, `sin web` |

## Mapa de fuentes de diseño

| source_id | chunk_id | versión/hash | uso en esta fábrica |
|---|---|---|---|
| SRC-BRIEF-USER-20260608 | BRIEF-OBJ, BRIEF-SCOPE, BRIEF-AGENTS, BRIEF-STACK, BRIEF-SOURCES | sha256:7d5c9cc6116b4709479935ae7db38de6455605d0338d2ef56aa7edeb3a0ef29d | Objetivo, audiencia, alcance, agentes requeridos, stack, fuentes y restricciones del usuario. |
| ANEXO_A_CONTRATOS_ARNES | A-01..A-15 | sha256:b4beb176bc547059584055093995b246047f41c949676a34b23e5d273d136af3 | Contratos ARNES, puerta única, AgentSpec, ToolSpec, PolicySpec, CycleState, EvidenceRecord y HarnessRunner. |
| ANEXO_B_PLANTILLAS_SDD | B-01..B-07 | sha256:7e94a95f6ed8e56a96a285c5f2ac904bf93146666170aa52d407e6a0cde1a3f5 | Flujo SDD extendido, autoridad de artefactos y plantillas de los cinco archivos. |
| ANEXO_C_GATES_EVALS_VALIDADORES | C-01..C-19 | sha256:45a9aec5e993c4765dfea7c36368d793392e2f22e669cde5d08d378f394c3905 | Estados cerrados, gates, ValidatorChain, coverage, evals y formato final. |
| ANEXO_D_RAG_MEMORIA_CACHE_APRENDIZAJE | D-01..D-15 | sha256:0a5243680d1ef1c9364c787e5d03ff3421aac2e1eac8af9c3dafef2265706c80 | RAG, context-pack, índices, cache, memoria limpia, aprendizaje gobernado y prompt-injection. |
| ANEXO_E_OPERABILIDAD_OBSERVABILIDAD_COSTOS | E-01..E-18 | sha256:5b77b8e55f5d32ca424e4cfed4a13d0ead47eb0c5f595c0ebacf9b0699e412cc | Logs, billing-ledger, circuit breakers, SLOs, handoff, incidentes y cierre de run. |


## 1. Vista ejecutiva

La fábrica se diseña como una línea de producción Spec-Driven, no como chatbot. Cada solicitud entra como `work_order`, pasa por especificación, recuperación de evidencia, planificación, tareas, análisis, implementación controlada, validación, observabilidad y cierre. ARNES/Harness contiene la ejecución: permisos, contexto, memoria, tools, presupuesto, validadores, logs y errores.

Objetivo operativo: producir entregables de software web crítico con documentación fuerte, pruebas medibles, seguridad por defecto, trazabilidad completa y reproducibilidad práctica `>=98%` en evals definidos. El diseño reduce variabilidad mediante schemas estrictos, temperatura `0`, snapshot fijo, cache, índices versionados, reranking fijo, tool allowlist y gates bloqueantes; no promete determinismo absoluto.

## 2. Arquitectura objetivo

```text
Fuentes autorizadas del proyecto
  ├─ Código fuente
  ├─ Metadata/dumps read-only de Oracle/PostgreSQL/MySQL
  ├─ Stored procedures/triggers/views/jobs/paquetes/funciones
  ├─ Documentación/tickets/issues/historias/manuales/diagramas
  ├─ Logs/trazas/pruebas/reportes
  └─ Brief/documentos autorizados
        ↓
API + WorkOrderRouter
        ↓
Spec Control Plane
        ↓
Context/RAG Layer + Index/Cache/Compression
        ↓
ARNES / HarnessRunner
        ↓
OrchestratorGraph
        ↓
Agent/Skill Layer
        ↓
ValidatorChain
        ↓
CI/CD dry-run + Sandbox
        ↓
Observability + Billing + Traceability
        ↓
Learning Governance + Handoff
```

## 3. Capas y responsabilidades

| capa | responsabilidad | no debe hacer | artefactos |
|---|---|---|---|
| API | Recibir `work_order`, validar contrato mínimo y autenticación del solicitante. | Decidir arquitectura o ejecutar agentes directo. | `work_order.json`, `request_log`. |
| WorkOrderRouter | Normalizar entrada, clasificar tipo de tarea/riesgo, seleccionar flujo SDD. | Implementar código o resolver contenido técnico libre. | `routing_decision.json`. |
| Spec Control Plane | Mantener Constitution, Specify, Clarify, Checklist, Plan, Tasks y Analyze como autoridad. | Saltar gates o permitir drift. | `constitution.md`, `spec.md`, `clarifications.md`, `plan.md`, `tasks.md`. |
| Context/RAG Layer | Construir `context-pack` mínimo con chunks, scores, hashes, dedupe, metadata y evidencia. | Decidir por intuición o pasar documentos completos. | `context-pack.json`, `evidence-register.json`. |
| Index/Cache/Compression | Versionar corpus, acelerar recuperación, compactar contexto y evitar tool calls repetidas. | Cachear secretos, tokens, PII sensible o resultados `policy_denied`. | índices vector/BM25/graph/spec/evidence, `cache-ledger`. |
| ARNES/HarnessRunner | Contener ejecución: permisos, contexto, memoria, tools, presupuesto, validadores, logs. | Delegar permisos al agente o aceptar outputs inválidos. | `CycleState`, `AgentResult`, `validation-report.json`. |
| OrchestratorGraph | Decidir transición de fases usando estados cerrados. | Llamar LLM/tool directo o generar contenido técnico. | `graph-state.json`, `run_state`. |
| Agent/Skill Layer | Ejecutar tareas acotadas con salida JSON/schema. | Asumir permisos, llamar agentes, escribir memoria sin gate. | `agent-output.json`, `tool-request.json`. |
| ValidatorChain | Aprobar, rechazar, bloquear o pedir input con evidencia. | Corregir silenciosamente sin issue trazable. | `validation-report.json`, `qa-report.json`. |
| CI/CD + Sandbox | Ejecutar lint, typecheck, tests, scans, builds y migraciones dry-run. | Merge/deploy/infra sin aprobación. | `test_report`, `coverage_report`, `security_review`. |
| Observability | Registrar logs, trazas, métricas, costos, latencia y circuit breakers. | Ocultar fallos o omitir ledger. | `log.jsonl`, `billing-ledger.json`, traces, dashboards. |
| Learning Governance | Proponer aprendizaje en `Aprendizaje.md` con aprobación, TTL, confidence y rollback. | Aprender automáticamente o inyectar memoria tainted. | `Aprendizaje.md`, `MemoryProposal`. |
| Storage | Persistir artefactos auditables y hashes. | Guardar secretos en claro. | `state.json`, reports, artifacts, indexes. |

## 4. Stack tecnológico de referencia

| capa | stack | validaciones obligatorias |
|---|---|---|
| Frontend | Next.js + React + TypeScript + Tailwind CSS + shadcn/ui | `eslint`, typecheck, tests unitarios/componentes, E2E, a11y, snapshots visuales cuando aplique. |
| Backend | Python 3 + FastAPI + Pydantic + SQLAlchemy + Alembic | `ruff/flake`, typecheck, tests unitarios/integración, OpenAPI validation, migraciones dry-run. |
| Base de datos | PostgreSQL, MySQL, MongoDB; Oracle como fuente read-only si legado | Introspección read-only, schema diff, explain plan no destructivo, tests de migración. |
| Cache/sesiones/rate limit | Redis | TTL, invalidación, tests de concurrencia, rate-limit tests. |
| Auth | OIDC/OAuth2 con Keycloak, Auth0, Clerk o similar | Threat model, scopes, claims, refresh/session policy, pruebas de autorización. |
| Infra | Docker + CI/CD + Cloudflare/CDN + PostgreSQL administrado | Build reproducible, SBOM, dependency scan, secrets scan, deploy dry-run. |
| Observabilidad | Sentry + OpenTelemetry + Prometheus + Grafana | Traces, métricas, alertas, SLOs, error budget, dashboards. |

Política: el stack de referencia no autoriza compatibilidad automática. Toda integración real requiere evidencia del repositorio, configuración, locks, metadata BD y restricciones del proyecto. Lo no evidenciado queda `TBD`.

## 5. Tipos de trabajo y routing

| tipo | condición de entrada | flujo | agentes principales | salida |
|---|---|---|---|---|
| `diseño_factory` | Solicitud de crear/ajustar fábrica | SDD diseño sin implementación | Spec, Arquitectura, QA, Documentación | 5 `.md` y handoff. |
| `auditoria_factory` | Revisión de fábrica existente | Context → Analyze → Validate → Close | Context/RAG, QA, Seguridad, Costos | informe de brechas. |
| `expansion_factory` | Agregar agentes/tools/policies | Specify → Plan → Tasks → Validate | Spec, Arquitectura, Seguridad | cambio propuesto dry-run. |
| `handoff` | Preparar transferencia técnica | Context → Docs → QA → Close | Documentación, QA, Observability | paquete handoff. |
| `feature_web` | Nuevo módulo o cambio funcional | SDD completo | Spec, Context, Arquitectura, Implementación, Tests, QA | plan/diff/tests/docs. |
| `mantencion_refactor` | Deuda técnica o mejora incremental | Context → Plan → Tasks → Analyze → Implement → Validate | Context, Arquitectura, Implementación, Tests, QA | diff dry-run y reporte. |
| `migracion_bd` | Cambio esquema/datos/motor | Context DB → Plan Validation → Tasks → Dry-run → Validate | DB/Legacy, Arquitectura, Tests, Seguridad | plan migración + rollback. |
| `api_segura` | Endpoint/contrato API | Specify → Contract → Security → Tests → Docs | API, Seguridad, Tests, Documentación | OpenAPI + ejemplos + tests. |
| `imagen_ocr` | Pantallas, mockups o diagramas | OCR → Context → Spec/Docs/QA | OCR, Spec, QA | extracción estructurada con confidence. |

## 6. Flujo SDD controlado

| fase | entrada | agente/skill | tool | gate | salida |
|---|---|---|---|---|---|
| Constitution | brief/work_order | `agent.spec` | `tool.file.read`, `tool.template.render` | `constitution` | `constitution.md` |
| Specify | objetivo+alcance | `agent.spec` | `tool.schema.validate` | `spec` | `spec.md` |
| Clarify | ambigüedades | `agent.spec` + skill `clarify.detect` | none/read-only | `clarification` | `clarifications.md` o `needs_user_input` |
| Checklist | spec | `agent.qa` | `tool.validator.chain` | `checklist` | `checklist.md` |
| Context Grounding | fuentes autorizadas | `agent.context_rag` | `tool.index.query`, `tool.cache.get/set`, `tool.code.search` | `context`, `evidence` | `context-pack.json` |
| Plan | spec+context | `agent.architecture_plan` | `tool.template.render`, `tool.openapi.validate` | `plan` | `plan.md` |
| Plan Validation | plan | `agent.qa` + `agent.security_policy` | `tool.validator.chain`, scanners | `plan_validation` | `plan-validation.json` |
| Tasks | plan validado | `agent.spec` + skill `tasks.slice` | `tool.schema.validate` | `tasks` | `tasks.md` |
| Analyze | spec+plan+tasks | `agent.qa` | `tool.consistency.validate` | `analyze` | `analyze-report.json` |
| Implement | tasks aprobadas | `agent.implementation` | `tool.diff.dry_run`, `tool.test.run_sandbox` | `sandbox`, `policy` | diff dry-run, docs in code |
| Validate | diff+tests | `agent.tests_coverage`, `agent.security_policy`, `agent.qa` | test/scans/coverage | `tests`, `coverage`, `security` | reports |
| PR/Deploy | validación completa | `agent.devops_observability` | CI/CD dry-run | `human_approval` | PR/deploy plan; no ejecución real sin aprobación |
| Observe | run/deploy report | `agent.devops_observability` | `tool.metrics.emit`, `tool.log.write` | `observability`, `budget` | traces, ledger, SLO report |
| Close | evidencia y gates | Orchestrator vía harness | none | `final_format` | `final-report.json`, handoff |

Reglas de avance:
- No se permite `Implement` sin `spec`, `clarify`, `checklist`, `context`, `plan`, `plan_validation`, `tasks` y `analyze` aprobados.
- Si un encargo es solo diseño, fases de implementación/PR/deploy se marcan `not_applicable` con razón.
- Cada requisito debe mapear a task, test, evidencia y gate.
- Toda ambigüedad crítica genera `needs_user_input`; toda decisión crítica sin evidencia genera `not_answerable`.

## 7. WorkOrder mínimo

```json
{
  "work_order_id": "WO-TBD",
  "objective": "TBD",
  "scope": {
    "include": ["TBD"],
    "exclude": ["TBD"]
  },
  "inputs": [
    {
      "source_id": "SRC-TBD",
      "type": "brief|repo|doc|ticket|log|db|memory|other",
      "path": "TBD",
      "authorized": true,
      "hash": "sha256:TBD"
    }
  ],
  "constraints": {
    "no_web": true,
    "dry_run": true,
    "max_retries": 2,
    "risk": "high",
    "max_cost_usd": 0,
    "max_latency_ms": 0
  },
  "expected_outputs": ["markdown", "reports", "traceability"],
  "approval_required_for": ["write", "deploy", "merge", "external_api", "secrets", "infra", "cost_increase", "data_access"]
}
```

## 8. RAG, índice, cache y compresión

### 8.1 Pipeline

```text
normalize_query
→ query_hash
→ cache.get(query_hash + corpus_hash + policy_version)
→ index.query(vector + keyword + metadata_filters)
→ score_threshold
→ rerank fijo
→ dedupe por source_id/chunk_hash
→ policy_filter
→ compact
→ build_context_pack
→ evidence_register
→ cache.set(context_pack_hash)
```

### 8.2 Índices requeridos

| índice | contenido | uso | invalidación |
|---|---|---|---|
| `idx.vector.docs` | docs, issues, specs, manuales, pantallas OCR | recuperación semántica | corpus/spec/policy changed |
| `idx.keyword.bm25` | nombres exactos, clases, tablas, endpoints, IDs | precisión | corpus changed |
| `idx.code.ast` | símbolos, imports, rutas, funciones, SQL embebido | mantenimiento/refactor | commit changed |
| `idx.db.schema` | tablas, constraints, views, triggers, procedures, jobs | migración/impacto | metadata dump changed |
| `idx.graph.entities` | entidades/relaciones módulos-tablas-endpoints | trazabilidad conceptual | corpus changed |
| `idx.evidence` | chunks citables con hash y version | auditoría | evidence invalidated |
| `idx.spec` | constitution/spec/plan/tasks/analyze | control SDD | spec changed |
| `idx.tool_results` | tests, scans, OCR, SQL explain, OpenAPI validation | evitar repeticiones | tool/env/input changed |
| `idx.memory` | memoria aprobada | aprendizaje gobernado | memory approved/expired |

### 8.3 Cache

| cache | key | TTL sugerido | no cachear |
|---|---|---:|---|
| prompt | `prompt_hash + model_snapshot` | largo | prompts con secretos |
| context | `repo_commit + index_version + query_hash + policy_version` | medio | chunks tainted |
| retrieval | `query_hash + corpus_hash + filters` | corto/medio | policy denied |
| tool_result | `tool_id + input_hash + env_hash + tool_version` | variable | datos productivos sensibles |
| test | `commit + suite + env_hash` | hasta commit | secretos o outputs privilegiados |
| validation | `artifact_hash + validator_version` | hasta cambio | outputs no validados |
| semantic | `normalized_query + policy_version` | corto | PII sensible |

### 8.4 Compactación

Orden: dedupe → eliminar bajo score → resumir evidencia no crítica → conservar citas/hashes → conservar claims relevantes → fallar si no cabe evidencia crítica. Prohibido eliminar `evidence_id` de claims críticos o mezclar fuentes contradictorias.

## 9. Flujos especializados

### 9.1 Documentación abundante y mantenimiento

```text
spec + context-pack
→ docs.inventory
→ docs.gap_analysis
→ docs.architecture
→ docs.api
→ docs.operations
→ docs.inline_code_comments_plan
→ docs.review_against_evidence
→ docs.handoff
```

Salidas:
- `README.md` por módulo cuando aplique.
- `ARCHITECTURE.md` o sección equivalente.
- `API.md` y OpenAPI.
- `RUNBOOK.md`.
- `DECISIONS.md`.
- Comentarios en código solo en diff dry-run, orientados a invariantes, contratos, edge cases y lógica no obvia.
- Mapa requisito→documento→evidencia.

Reglas:
- No documentar features no evidenciadas.
- No introducir comentarios que repliquen lo obvio.
- Comentarios de mantenimiento deben explicar intención, restricciones, riesgos y enlaces a spec/task/evidence.
- Toda documentación generada pasa `EvidenceValidator` y `ConsistencyValidator`.

### 9.2 Refactorización incremental

```text
context-pack(code+tests+logs)
→ debt_map
→ risk_slice
→ plan incremental
→ task atómica
→ diff dry-run
→ tests baseline/regression
→ coverage/security/dependency
→ docs update
→ handoff
```

Controles:
- Mantener comportamiento observable salvo spec aprobada indique cambio.
- Usar characterization tests antes de tocar código legado.
- Un refactor por unidad pequeña; cada diff mapea a task y rollback.
- Bloquear si no existe prueba para comportamiento crítico.

### 9.3 Migración y BD

```text
metadata read-only
→ object inventory
→ dependency graph
→ data risk classification
→ compatibility analysis
→ migration plan
→ Alembic/schema diff dry-run
→ rollback plan
→ tests
→ approval gate
```

Reglas:
- No DDL/DML real sin aprobación.
- No asumir compatibilidad Oracle/PostgreSQL/MySQL/MongoDB.
- Stored procedures/triggers/jobs deben tener hash, dependencias y casos de prueba.
- Volumen, cardinalidad, locks, downtime y SLO quedan `TBD` si no hay evidencia.

### 9.4 API segura con tokens y ejemplos

```text
spec endpoint
→ auth requirements
→ OpenAPI contract
→ Pydantic schemas
→ scopes/claims/errors/rate limits
→ examples
→ contract tests
→ security review
→ docs
```

Controles:
- OIDC/OAuth2; provider `TBD` hasta evidencia/aprobación.
- Tokens y secretos no entran al prompt.
- Documentar ejemplos sin credenciales reales.
- Tests mínimos: auth required, forbidden, invalid token, expired token, scope missing, rate-limit, schema validation, idempotency cuando aplique.

### 9.5 OCR / imágenes / pantallas

```text
image_input
→ hash + metadata
→ OCR/layout extraction
→ confidence scoring
→ prompt-injection scan visual/textual
→ structured findings
→ human review si confidence baja
→ mapear a spec/docs/tests
```

Controles:
- OCR no decide reglas de negocio; solo aporta evidencia visual.
- Texto extraído se trata como input no confiable.
- Si una pantalla contradice código/spec, se lista conflicto y se bloquea decisión.

### 9.6 Validación y QA práctico

```text
requirements
→ acceptance criteria
→ test matrix
→ implementation diff
→ unit/integration/contract/E2E/security/performance/a11y
→ coverage
→ defect triage
→ release decision
```

QA no aprueba su propio trabajo de implementación. El gate de QA exige checklist práctico, casos negativos, regresión, datos de prueba, evidencia y reporte reproducible.

## 10. CI/CD y gates técnicos

| etapa | herramienta esperada | gate | bloqueo |
|---|---|---|---|
| Format/lint frontend | `eslint`, formatter aprobado | `tests` | errores lint críticos |
| Typecheck frontend | TypeScript | `tests` | tipos rotos |
| Tests frontend | runner aprobado `TBD` | `coverage` | cobertura menor a umbral |
| Backend lint | `ruff/flake` o equivalente aprobado | `tests` | errores críticos |
| Typecheck backend | `mypy/pyright` o equivalente aprobado | `tests` | tipos rotos |
| Unit tests | pytest/runner aprobado | `tests` | fail |
| Integration tests | DB/cache/auth sandbox | `tests` | fail |
| Contract tests | OpenAPI/Pact equivalente aprobado | `contract` | drift |
| E2E | Playwright/Cypress equivalente aprobado | `tests` | flujos críticos fail |
| Coverage | coverage reports | `coverage` | umbral no alcanzado |
| Security scan | SAST/dependency/secrets | `security`, `secrets`, `dependency` | high/critical abierto |
| Migration dry-run | Alembic/schema diff/explain | `sandbox`, `human_approval` | destructive risk |
| Build | Docker reproducible | `dependency` | build fail |
| AI evals | eval runner determinístico | `evals` | estabilidad < target |
| PR/deploy | CI/CD | `human_approval` | sin aprobación |

## 11. Escalabilidad, eficiencia y eficacia

| objetivo | mecanismo |
|---|---|
| Menos agentes | Router usa skill determinística si basta; agentes solo separan permisos/riesgo/evals/memoria. |
| Menos contexto | Context-pack mínimo; compresión con conservación de evidence_id; no historial completo. |
| Menos tool calls | Cache antes de index; tool result cache; batch de lecturas; no repetir tests si input/env no cambió. |
| Menor latencia | Rerank fijo acotado, circuit breakers, timeouts, parallelismo solo para tools determinísticas cuando policy lo permita. |
| Menor costo | `BudgetManager`, budgets por fase/agente/tool, ledger y degradación controlada. |
| Mayor calidad | SDD obligatorio, gates, tests, coverage, revisión QA independiente, seguridad y observabilidad. |
| Mantenibilidad | Documentación técnica, decisiones, comentarios de código y trazabilidad. |
| Alta disponibilidad | Diseño con SLOs, observabilidad, rollback, rate limit, cache, CDN e infra aprobada. |

## 12. Arquitectura de pruebas

| nivel | propósito | evidencia | gate |
|---|---|---|---|
| Unit | lógica aislada | `unit_test_report` | `tests` |
| Component | UI/servicios por componente | `component_test_report` | `tests` |
| Integration | API+DB+cache/auth sandbox | `integration_report` | `tests` |
| Contract | OpenAPI, schemas, consumer/provider | `contract_report` | `contract` |
| E2E | flujos críticos usuario/sistema | `e2e_report` | `tests` |
| Regression | comportamiento legado | `regression_report` | `coverage` |
| Characterization | capturar comportamiento antes de refactor | `characterization_report` | `analyze` |
| Migration | schema/data dry-run/rollback | `migration_report` | `sandbox` |
| Security | auth, secrets, dependency, SAST | `security_review` | `security` |
| Performance | carga/latencia/capacidad | `perf_report` | `observability` |
| Accessibility | a11y UI | `a11y_report` | `QA` |
| Mutation | fortaleza de tests cuando aplique | `mutation_report` | `coverage` |

El objetivo de 100% se aplica como release gate sobre requisitos críticos y cobertura definida. Si se pide 100% line/branch/function, debe configurarse en el `work_order` o quedar `TBD` hasta aprobación.

## 13. Handoff técnico

Paquete mínimo de handoff por run:
- `RUN_STATE.md`
- `DECISIONS.md`
- `ERRORS.md`
- `TASKS.md`
- `traceability-matrix.md`
- `validation-report.json`
- `security-review.md`
- `billing-ledger.json`
- `final-report.json`
- `Aprendizaje.md` con propuestas, no aprendizaje automático
- diffs dry-run y reportes de tests/scans si aplica

## 14. Roadmap de implementación de la fábrica

| fase | objetivo | criterio de término |
|---|---|---|
| 1 | Spec-first básico | `work_order`, constitution/spec/plan/tasks y gates manuales. |
| 2 | ARNES mínimo | `HarnessRunner`, registries, PolicyEngine, ValidatorChain y logs. |
| 3 | RAG/index/cache | Context-pack, evidence register, corpus hash, retrieval reproducible. |
| 4 | Agentes controlados | AgentSpec/ToolSpec por agente, output schema y evals. |
| 5 | CI/CD y sandbox | tests/scans/dry-run reproducibles, no side effects. |
| 6 | Observabilidad/costos | ledger, traces, dashboards, circuit breakers. |
| 7 | Learning Governance | `Aprendizaje.md`, MemoryGate, TTL, approval, rollback. |
| 8 | Plataforma enterprise | multi-repo, multi-proyecto, auditoría, RBAC, SLOs y reporting. |

## 15. Riesgos y mitigaciones

| riesgo | mitigación | estado |
|---|---|---|
| Alucinación/invención | EvidenceValidator, `not_answerable`, no memoria no validada. | diseñado |
| Prompt injection en docs/logs/OCR | Treat-as-data, quarantine, safety gate. | diseñado |
| Variabilidad del modelo | snapshot fijo, temperature 0, schemas, evals, cache. | diseñado |
| Costos altos | BudgetManager, cache, mínimos agentes/tool calls. | diseñado |
| Latencia alta | context compact, cache, timeouts, circuit breakers. | diseñado |
| Cambios destructivos | dry-run, sandbox, human approval. | diseñado |
| Cobertura superficial | coverage + contract + E2E + mutation/characterization. | diseñado |
| Dependencias riesgosas | dependency gate, SBOM, aprobación. | diseñado |


## 16. Consistencia transversal ARNES/SDD

- Estados cerrados obligatorios en todo flujo: `complete`, `needs_user_input`, `not_answerable`, `error`.
- El orquestador de esta arquitectura no ejecuta agentes directamente; toda ejecución pasa por `harness.run_agent(agent_id, state)`.
- Cada fase conserva trazabilidad `spec_id → task_id → evidence_id → test_id → gate_id`.
- Los fallbacks son obligatorios: `needs_user_input` ante falta de dato/permiso/aprobación, `not_answerable` ante falta de evidencia crítica, `error` ante fallo no reparable y `complete` solo con gates aprobados.
