# Agentes, Skills, Herramientas y Permisos

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

## 1. Regla de agentes mínimos

Crear un agente solo si separa al menos una de estas dimensiones: responsabilidad, permisos, memoria, tools, riesgo, evaluación, presupuesto, artefactos o independencia de QA. Si una skill determinística puede resolver la tarea con schema y tool allowlist, no se crea agente adicional.

La fábrica usa agentes como unidades de responsabilidad controladas por ARNES. Las skills son funciones determinísticas o procedimientos acotados; las tools son capacidades concretas allowlisted; los validadores aprueban o bloquean. Ningún agente decide sus propios permisos.

## 2. Registro mínimo de agentes

| agente | usar cuando | no usar cuando | inputs | outputs | tools | permisos | gates | budget |
|---|---|---|---|---|---|---|---|---|
| `agent.orchestrator` | Coordinar flujo y transición SDD. | Generar contenido técnico libre. | `CycleState` | routing decision | ninguna directa | `flow_only` | `policy`, `budget` | bajo |
| `agent.spec` | Definir objetivo, requisitos, aclaraciones, acceptance criteria y tasks. | Faltan objetivo o fuentes críticas. | brief, work_order, context-pack | spec/clarifications/tasks JSON | `tool.schema.validate`, `tool.template.render` | write spec artifacts | `spec`, `clarification`, `schema` | medio |
| `agent.context_rag` | Recuperar evidencia de código/docs/BD/logs/OCR. | La decisión ya tiene context-pack fresco. | queries, source registry | context-pack, evidence records | `tool.index.query`, `tool.cache.get/set`, `tool.code.search`, `tool.db.metadata_readonly` | read-only | `context`, `evidence`, `safety` | medio |
| `agent.architecture_plan` | Diseñar arquitectura, plan técnico, migración y refactor incremental. | No hay spec o evidencia mínima. | spec, context-pack, constraints | plan, risk register, migration plan | `tool.template.render`, `tool.openapi.validate`, `tool.dependency.check` | write plan only | `plan`, `plan_validation` | alto |
| `agent.documentation` | Generar documentación técnica, handoff y docs dentro del código. | Feature no evidenciada. | spec, plan, tasks, evidence, diff | docs, inline-doc plan, handoff | `tool.docs.render`, `tool.diff.read`, `tool.schema.validate` | write docs/dry-run | `documentation`, `evidence`, `consistency` | bajo |
| `agent.tests_coverage` | Crear plan de pruebas, ejecutar suites sandbox y revisar cobertura. | Aprobar trabajo propio de implementación. | spec, tasks, diff, test config | test plan, test report, coverage report | `tool.test.run_sandbox`, `tool.coverage.report`, `tool.mutation.run_dry` | run tests sandbox | `tests`, `coverage` | medio |
| `agent.implementation` | Producir diff dry-run según tasks aprobadas con documentación en código. | Definir requisitos o aprobar su propio diff. | tasks, context-pack, plan | patch/diff dry-run, code docs | `tool.diff.dry_run`, `tool.code.search`, `tool.test.run_sandbox` | sandbox write draft only | `sandbox`, `tests`, `policy` | alto |
| `agent.ocr_image` | Analizar pantallas, mockups, diagramas o imágenes autorizadas. | Imagen no autorizada o contiene secretos no redactados. | image, metadata, objective | OCR/layout JSON, evidence candidates | `tool.ocr.extract`, `tool.image.layout`, `tool.safety.scan_text` | read image only | `safety`, `evidence`, `schema` | medio |
| `agent.api_secure` | Diseñar/generar contratos API seguros con tokens y ejemplos. | Auth/provider/scopes no evidenciados y decisión es crítica. | spec, auth constraints, data schemas | OpenAPI, examples, auth matrix, tests | `tool.openapi.validate`, `tool.schema.validate`, `tool.security.scan` | write contract docs | `contract`, `security`, `tests` | medio |
| `agent.qa` | Revisar consistencia, checklist práctico, gates finales y release decision. | Corregir silenciosamente sin issue. | all artifacts/reports | QA report, decision | `tool.validator.chain`, `tool.traceability.check` | approve/block | `QA`, `final_format`, `coverage` | medio |
| `agent.security_policy` | Revisar seguridad, permisos, dependencias, secretos, prompt injection. | Desplegar o escribir secretos. | artifacts, tool requests, diff | security review, policy decision | `tool.secrets.scan`, `tool.dependency.scan`, `tool.sast.scan`, `tool.policy.evaluate` | block/require approval | `security`, `secrets`, `dependency`, `policy` | medio |
| `agent.db_legacy` | Analizar SQL, metadata, stored procedures, triggers, views, jobs y migración. | Ejecutar DDL/DML real. | metadata read-only, SQL, schema dumps | DB inventory, impact map, migration risks | `tool.sql.parse`, `tool.db.metadata_readonly`, `tool.schema.diff_dry_run` | read-only/dry-run | `context`, `sandbox`, `safety` | medio |
| `agent.devops_observability` | Definir CI/CD, logs, SLOs, dashboards, cost ledger y handoff operativo. | Merge/deploy/infra real sin aprobación. | plan, tests, infra constraints | CI/CD plan, observability plan, runbook | `tool.log.write`, `tool.metrics.emit`, `tool.ci.validate_dry_run` | dry-run only | `observability`, `budget`, `human_approval` | medio |
| `agent.cost_optimizer` | Optimizar tokens, tool calls, cache, latency y budget. | Cambiar contenido técnico sin spec. | ledger, context stats, tool logs | cost report, optimization plan | `tool.billing.compute`, `tool.cache.stats`, `tool.trace.analyze` | read logs | `budget`, `observability` | bajo |

## 3. Fichas AgentSpec

### 3.1 `agent.spec`

```yaml
agent_id: "agent.spec"
agent_name: "Agente de especificación detallada"
version: "0.1.0"
status: "draft"
purpose: "Convertir brief/work_order/evidencia en especificación, aclaraciones, acceptance criteria y tasks trazables."
single_responsibility: "Gobierno de requisitos y división de trabajo SDD."
use_when:
  - "Se requiere constitution, spec, clarify, checklist o tasks."
  - "Hay cambios funcionales o técnicos que necesitan aceptación verificable."
do_not_use_when:
  - "Falta objetivo verificable."
  - "La decisión depende de evidencia no recuperada."
inputs:
  - "work_order"
  - "brief"
  - "context_pack"
outputs:
  - "spec.json"
  - "clarifications.md"
  - "tasks.md"
allowed_tools:
  - "tool.schema.validate"
  - "tool.template.render"
  - "tool.traceability.check"
permissions:
  read_repo: false
  write_files: false
  write_artifacts: true
  run_tests: false
  external_api: false
  deploy: false
  read_secrets: false
  write_memory: false
model_policy:
  model: "gpt-5.5-or-fixed-snapshot"
  temperature: 0
  top_p: 1
  seed: 12345
  parallel_tool_calls: false
  response_format: "strict_json_schema"
budget:
  max_input_tokens: 12000
  max_output_tokens: 3000
  max_tool_calls: 2
  max_retries: 1
  timeout_ms: 30000
gates: ["schema", "spec", "clarification", "evidence", "budget"]
memory_policy:
  read_scopes: ["factory", "project"]
  write_allowed: false
learning_policy: "propose_only"
rollback: "discard_agent_output"
evals: ["E01", "E02", "E04", "E14"]
```

### 3.2 `agent.documentation`

```yaml
agent_id: "agent.documentation"
agent_name: "Agente de documentación técnica detallada"
version: "0.1.0"
status: "draft"
purpose: "Generar documentación técnica, handoff y documentación dentro del código con evidencia."
single_responsibility: "Documentación mantenible, verificable y no inventada."
use_when:
  - "Se requiere README, ARCHITECTURE, API, RUNBOOK, DECISIONS, handoff o comentarios de mantenimiento."
  - "Hay diff dry-run que requiere documentación en código."
do_not_use_when:
  - "No existe spec/task/evidence."
  - "Se busca inventar documentación de features no implementadas."
inputs:
  - "spec"
  - "plan"
  - "tasks"
  - "context_pack"
  - "diff_dry_run"
outputs:
  - "docs_bundle"
  - "inline_doc_plan"
  - "handoff_notes"
allowed_tools:
  - "tool.docs.render"
  - "tool.diff.read"
  - "tool.schema.validate"
  - "tool.traceability.check"
permissions:
  read_repo: true
  write_files: false
  write_artifacts: true
  run_tests: false
  external_api: false
  deploy: false
  read_secrets: false
  write_memory: false
gates: ["schema", "evidence", "consistency", "documentation", "final_format"]
budget:
  max_input_tokens: 10000
  max_output_tokens: 4000
  max_tool_calls: 2
  max_retries: 1
memory_policy:
  read_scopes: ["factory", "project"]
  write_allowed: false
learning_policy: "propose_only"
rollback: "discard_docs_bundle"
evals: ["E01", "E04", "E07", "E14"]
```

### 3.3 `agent.tests_coverage`

```yaml
agent_id: "agent.tests_coverage"
agent_name: "Agente de tests, planes y ejecución con cobertura"
version: "0.1.0"
status: "draft"
purpose: "Diseñar test matrix, ejecutar pruebas en sandbox y validar cobertura definida."
single_responsibility: "Calidad verificable por pruebas; no aprobación final de su propio trabajo."
use_when:
  - "Se requiere plan de pruebas, ejecución de suites, coverage, regression, contract, E2E o mutation."
do_not_use_when:
  - "No hay spec/task trazable."
  - "Se necesita aprobar release final sin QA independiente."
inputs:
  - "spec"
  - "tasks"
  - "diff_dry_run"
  - "test_config"
  - "environment_hash"
outputs:
  - "test_plan.json"
  - "test_report.json"
  - "coverage_report.json"
  - "gaps.md"
allowed_tools:
  - "tool.test.run_sandbox"
  - "tool.coverage.report"
  - "tool.mutation.run_dry"
  - "tool.openapi.validate"
  - "tool.traceability.check"
permissions:
  read_repo: true
  write_files: false
  write_artifacts: true
  run_tests: true
  external_api: false
  deploy: false
  read_secrets: false
  write_memory: false
gates: ["tests", "coverage", "schema", "budget", "sandbox"]
coverage_policy:
  requirements_critical: "100%"
  changed_files_with_tests: "100%"
  line_branch_function: "TBD por proyecto"
  mutation_threshold: "TBD por proyecto"
budget:
  max_input_tokens: 8000
  max_output_tokens: 2000
  max_tool_calls: 4
  max_retries: 1
evals: ["E01", "E09", "E10", "E14"]
```

### 3.4 `agent.implementation`

```yaml
agent_id: "agent.implementation"
agent_name: "Agente de implementación con documentación en código"
version: "0.1.0"
status: "draft"
purpose: "Producir diffs dry-run basados en tasks aprobadas y agregar documentación en código solo cuando ayuda al mantenimiento."
single_responsibility: "Ejecución técnica acotada, no definición de requisitos."
use_when:
  - "Existe task atómica aprobada, plan validado y contexto suficiente."
do_not_use_when:
  - "Falta analyze aprobado."
  - "El cambio requiere side effects no aprobados."
  - "El agente sería juez de su propio trabajo."
inputs:
  - "task"
  - "plan"
  - "context_pack"
  - "coding_standards"
outputs:
  - "diff_dry_run"
  - "implementation_notes"
  - "inline_doc_changes"
allowed_tools:
  - "tool.code.search"
  - "tool.ast.parse"
  - "tool.diff.dry_run"
  - "tool.test.run_sandbox"
  - "tool.schema.validate"
permissions:
  read_repo: true
  write_files: false
  write_dry_run: true
  run_tests: true
  external_api: false
  deploy: false
  read_secrets: false
  write_memory: false
gates: ["schema", "policy", "sandbox", "tests", "coverage", "security"]
budget:
  max_input_tokens: 16000
  max_output_tokens: 5000
  max_tool_calls: 4
  max_retries: 1
rollback: "discard_diff"
evals: ["E06", "E08", "E10", "E13"]
```

### 3.5 `agent.ocr_image`

```yaml
agent_id: "agent.ocr_image"
agent_name: "Agente OCR para análisis de imágenes"
version: "0.1.0"
status: "draft"
purpose: "Extraer texto, estructura visual y señales de pantallas/diagramas autorizados."
single_responsibility: "Convertir imagen autorizada en evidencia estructurada con confidence."
use_when:
  - "Hay pantallas, mockups, diagramas, capturas o flujos visuales."
do_not_use_when:
  - "La imagen contiene secretos no redactados."
  - "Se pretende inferir regla de negocio crítica sin confirmación."
inputs:
  - "image"
  - "image_metadata"
  - "analysis_objective"
outputs:
  - "ocr_result.json"
  - "layout_result.json"
  - "evidence_candidates.json"
allowed_tools:
  - "tool.ocr.extract"
  - "tool.image.layout"
  - "tool.safety.scan_text"
permissions:
  read_images: true
  write_artifacts: true
  external_api: false
  read_secrets: false
gates: ["schema", "safety", "evidence", "policy"]
budget:
  max_input_tokens: 4000
  max_output_tokens: 2000
  max_tool_calls: 3
evals: ["E04", "E07", "E10"]
```

### 3.6 `agent.api_secure`

```yaml
agent_id: "agent.api_secure"
agent_name: "Agente de generación de APIs seguras"
version: "0.1.0"
status: "draft"
purpose: "Diseñar contratos API seguros con tokens, ejemplos y pruebas."
single_responsibility: "Contratos API, auth matrix, OpenAPI y tests de contrato."
use_when:
  - "Se requiere endpoint, API pública/privada, contrato OpenAPI o documentación con ejemplos."
do_not_use_when:
  - "No hay evidencia de modelo de datos o reglas de autorización."
inputs:
  - "spec"
  - "data_schema"
  - "auth_policy"
  - "context_pack"
outputs:
  - "openapi.yaml"
  - "api_examples.md"
  - "auth_matrix.md"
  - "contract_tests_plan.json"
allowed_tools:
  - "tool.openapi.validate"
  - "tool.schema.validate"
  - "tool.security.scan"
  - "tool.docs.render"
permissions:
  read_repo: true
  write_artifacts: true
  external_api: false
  deploy: false
  read_secrets: false
gates: ["schema", "contract", "security", "tests", "evidence"]
budget:
  max_input_tokens: 10000
  max_output_tokens: 3000
  max_tool_calls: 3
evals: ["E01", "E04", "E07", "E13"]
```

### 3.7 `agent.qa`

```yaml
agent_id: "agent.qa"
agent_name: "Agente QA con checklist de pruebas prácticas"
version: "0.1.0"
status: "draft"
purpose: "Validar consistencia, cobertura, checklist práctico, riesgos y formato final."
single_responsibility: "Aprobar o bloquear; no implementar ni corregir silenciosamente."
use_when:
  - "Se requiere checklist, analyze report, release decision o cierre."
do_not_use_when:
  - "Se le pide implementar cambios."
inputs:
  - "spec"
  - "plan"
  - "tasks"
  - "diff"
  - "test_reports"
  - "security_review"
  - "billing_ledger"
outputs:
  - "qa_report.json"
  - "checklist.md"
  - "blocking_issues.md"
allowed_tools:
  - "tool.validator.chain"
  - "tool.traceability.check"
  - "tool.schema.validate"
permissions:
  approve_block: true
  write_artifacts: true
  read_repo: true
  run_tests: false
  deploy: false
  read_secrets: false
gates: ["schema", "evidence", "consistency", "coverage", "budget", "final_format"]
budget:
  max_input_tokens: 12000
  max_output_tokens: 3000
  max_tool_calls: 3
evals: ["E01", "E02", "E03", "E04", "E05", "E12", "E14"]
```

## 4. Skills determinísticas

| skill_id | tipo | propósito | tool_id | input_schema | output_schema | deterministic | timeout_ms | retry | cache |
|---|---|---|---|---|---|---|---:|---:|---|
| `skill.work_order.normalize` | validate | Normalizar input a WorkOrder. | `tool.schema.validate` | `WorkOrderDraft` | `WorkOrder` | true | 5000 | 1 | no |
| `skill.source.hash` | compute | Calcular hashes de fuentes. | `tool.hash.compute` | `path/blob` | `hash_record` | true | 10000 | 1 | sí |
| `skill.rag.retrieve_context` | retrieval | Recuperar context-pack mínimo. | `tool.index.query` | `query+filters` | `context_pack` | true | 15000 | 1 | sí |
| `skill.cache.lookup` | compute | Consultar cache antes de tool costosa. | `tool.cache.get` | `cache_key` | `cache_record|null` | true | 1000 | 0 | sí |
| `skill.cache.store` | compute | Guardar resultado cacheable. | `tool.cache.set` | `cache_record` | `cache_status` | true | 1000 | 0 | sí |
| `skill.context.compact` | compute | Compactar contexto conservando evidencia. | `tool.context.compact` | `chunks+budget` | `compacted_context` | true | 5000 | 1 | sí |
| `skill.code.search_symbols` | retrieval | Buscar símbolos, rutas, imports y referencias. | `tool.code.search` | `repo+query` | `code_refs` | true | 10000 | 1 | sí |
| `skill.ast.parse` | compute | Parsear TS/Python/SQL donde aplique. | `tool.ast.parse` | `file_refs` | `ast_summary` | true | 10000 | 1 | sí |
| `skill.sql.parse` | compute | Parsear SQL embebido/procedures/triggers. | `tool.sql.parse` | `sql_text` | `sql_ast+dependencies` | true | 10000 | 1 | sí |
| `skill.db.introspect_readonly` | retrieval | Extraer metadata BD sin datos sensibles. | `tool.db.metadata_readonly` | `connection_metadata|dump` | `db_inventory` | true | 30000 | 1 | sí |
| `skill.openapi.validate` | validate | Validar contrato OpenAPI. | `tool.openapi.validate` | `openapi_doc` | `validation_result` | true | 10000 | 1 | sí |
| `skill.test.plan_coverage` | compute | Mapear requisitos a pruebas y cobertura. | `tool.traceability.check` | `spec+tasks` | `test_matrix` | true | 10000 | 1 | sí |
| `skill.test.run_sandbox` | test | Ejecutar tests autorizados. | `tool.test.run_sandbox` | `suite+env_hash` | `test_report` | true | 120000 | 1 | sí |
| `skill.coverage.read` | validate | Leer cobertura y comparar umbrales. | `tool.coverage.report` | `coverage_files+thresholds` | `coverage_decision` | true | 10000 | 0 | sí |
| `skill.security.scan` | validate | Escanear secretos, deps y SAST. | `tool.security.scan` | `diff/artifacts` | `security_findings` | true | 60000 | 1 | sí |
| `skill.ocr.extract` | retrieval | Extraer texto de imagen. | `tool.ocr.extract` | `image_ref` | `ocr_result` | true | 30000 | 1 | sí |
| `skill.docs.render` | file_write_dry_run | Renderizar docs desde templates. | `tool.docs.render` | `template+data` | `docs_bundle` | true | 10000 | 1 | sí |
| `skill.diff.generate_dry_run` | file_write_dry_run | Producir patch sin aplicar. | `tool.diff.dry_run` | `task+context` | `patch_preview` | true | 30000 | 1 | no |
| `skill.billing.compute` | observe | Calcular costos/tokens/latencia. | `tool.billing.compute` | `logs` | `billing_ledger` | true | 5000 | 0 | sí |
| `skill.validator.chain` | validate | Ejecutar ValidatorChain en orden. | `tool.validator.chain` | `artifact+schema+evidence` | `validation_report` | true | 15000 | 1 | no |

## 5. ToolRegistry allowlist

| tool_id | propósito | input_schema | output_schema | permisos | timeout_ms | retries | costo | side_effects | sandbox | errores | logs |
|---|---|---|---|---|---:|---:|---|---|---|---|---|
| `tool.file.read` | Leer archivos autorizados. | `FileReadInput` | `FileReadOutput` | read-only | 10000 | 1 | free | read | true | `file_not_found`, `policy_denied` | run/cycle/tool/input_hash/output_hash |
| `tool.hash.compute` | Calcular sha256. | `HashInput` | `HashOutput` | read-only | 5000 | 0 | free | none | true | `hash_error` | hashes |
| `tool.index.build` | Crear/actualizar índices. | `IndexBuildInput` | `IndexBuildOutput` | read-only/write index | 120000 | 1 | medium | write internal | true | `index_error` | index_version/corpus_hash |
| `tool.index.query` | Consultar índices. | `IndexQueryInput` | `ContextCandidates` | read-only | 15000 | 1 | low | read | true | `no_results`, `index_unavailable` | query_hash/scores |
| `tool.cache.get` | Consultar cache. | `CacheGetInput` | `CacheGetOutput` | read cache | 1000 | 0 | free | read | true | `cache_miss`, `cache_error` | cache_hit |
| `tool.cache.set` | Escribir cache permitida. | `CacheSetInput` | `CacheSetOutput` | write cache | 1000 | 0 | free | write internal | true | `cache_policy_denied` | cache_key/hash |
| `tool.context.compact` | Compactar context-pack. | `ContextCompactInput` | `ContextCompactOutput` | compute | 5000 | 1 | free | none | true | `critical_evidence_overflow` | context_hash |
| `tool.code.search` | Buscar en repo por símbolos/texto. | `CodeSearchInput` | `CodeSearchOutput` | read_repo | 10000 | 1 | low | read | true | `repo_unavailable` | source_refs |
| `tool.ast.parse` | Parsear código. | `AstParseInput` | `AstParseOutput` | read_repo | 10000 | 1 | low | read | true | `parse_error` | file_hashes |
| `tool.sql.parse` | Parsear SQL. | `SqlParseInput` | `SqlParseOutput` | read_sql | 10000 | 1 | low | read | true | `sql_parse_error` | object_refs |
| `tool.db.metadata_readonly` | Leer metadata/dump BD. | `DbMetadataInput` | `DbInventory` | read_db_metadata | 30000 | 1 | medium | read | true | `db_access_denied`, `metadata_error` | db_source/hash |
| `tool.schema.diff_dry_run` | Simular schema diff/migración. | `SchemaDiffInput` | `MigrationDryRunOutput` | dry_run | 60000 | 1 | medium | none | true | `destructive_change_detected` | migration_id |
| `tool.diff.dry_run` | Generar patch sin aplicar. | `DiffInput` | `DiffPreview` | write_dry_run | 30000 | 1 | low | none | true | `patch_conflict`, `policy_denied` | diff_hash |
| `tool.test.run_sandbox` | Ejecutar tests. | `TestRunInput` | `TestReport` | run_tests | 120000 | 1 | medium | none | true | `test_fail`, `timeout` | suite/env/hash |
| `tool.coverage.report` | Leer/reporte cobertura. | `CoverageInput` | `CoverageReport` | read reports | 10000 | 0 | low | read | true | `coverage_missing` | coverage_hash |
| `tool.mutation.run_dry` | Mutation testing si aprobado. | `MutationInput` | `MutationReport` | run_tests | 300000 | 0 | high | none | true | `budget_exceeded` | mutation_hash |
| `tool.openapi.validate` | Validar OpenAPI. | `OpenApiInput` | `OpenApiValidation` | compute | 10000 | 1 | low | none | true | `openapi_invalid` | contract_hash |
| `tool.docs.render` | Renderizar docs desde templates. | `DocsInput` | `DocsOutput` | write_artifacts | 10000 | 1 | low | write internal | true | `template_error` | docs_hash |
| `tool.validator.chain` | Ejecutar validadores. | `ValidationInput` | `ValidationReport` | validate | 15000 | 1 | low | none | true | `validation_fail` | validator_ids |
| `tool.traceability.check` | Verificar mappings spec-task-test-evidence. | `TraceabilityInput` | `TraceabilityReport` | validate | 10000 | 1 | low | none | true | `traceability_gap` | matrix_hash |
| `tool.policy.evaluate` | Evaluar permisos. | `PolicyInput` | `PolicyDecision` | policy | 5000 | 0 | low | none | true | `policy_denied` | policy_version |
| `tool.secrets.scan` | Detectar secretos. | `ScanInput` | `SecretsReport` | scan | 30000 | 1 | medium | read | true | `secret_detected` | scan_hash |
| `tool.dependency.scan` | Analizar dependencias/SBOM. | `DependencyInput` | `DependencyReport` | scan | 60000 | 1 | medium | read | true | `dependency_risk` | sbom_hash |
| `tool.sast.scan` | Análisis estático de seguridad. | `SastInput` | `SastReport` | scan | 60000 | 1 | medium | read | true | `sast_high` | scan_hash |
| `tool.ocr.extract` | OCR de imagen autorizada. | `OcrInput` | `OcrOutput` | read_images | 30000 | 1 | medium | read | true | `ocr_low_confidence` | image_hash |
| `tool.image.layout` | Extraer estructura visual. | `ImageLayoutInput` | `LayoutOutput` | read_images | 30000 | 1 | medium | read | true | `layout_error` | image_hash |
| `tool.safety.scan_text` | Detectar prompt injection/PII/secrets en texto. | `SafetyScanInput` | `SafetyScanOutput` | scan | 10000 | 1 | low | none | true | `prompt_injection_detected` | finding_ids |
| `tool.ci.validate_dry_run` | Validar pipeline sin merge/deploy. | `CiDryRunInput` | `CiDryRunOutput` | dry_run | 120000 | 1 | medium | none | true | `ci_fail` | pipeline_hash |
| `tool.log.write` | Escribir logs internos. | `LogInput` | `LogOutput` | write internal logs | 1000 | 1 | free | write internal | true | `log_write_error` | log_id |
| `tool.metrics.emit` | Emitir métricas internas. | `MetricsInput` | `MetricsOutput` | write internal metrics | 1000 | 0 | low | write internal | true | `metrics_error` | metric_id |
| `tool.billing.compute` | Calcular ledger. | `BillingInput` | `BillingLedger` | read logs | 5000 | 0 | low | none | true | `billing_error` | ledger_hash |
| `tool.trace.analyze` | Analizar latencia/tool calls. | `TraceInput` | `TraceAnalysis` | read logs | 10000 | 0 | low | read | true | `trace_missing` | trace_hash |

## 6. Herramientas prohibidas por defecto

- `shell.free`
- `secrets.read`
- `deploy.direct`
- `merge.direct`
- `db.write`
- `db.drop`
- `external_api.unapproved`
- `memory.write_ungated`
- `internet.web_unapproved`
- `file.write_external`
- instalación de dependencias sin aprobación
- lectura de historial completo
- comunicación libre entre agentes

## 7. Matriz de permisos

| permiso | default | requiere aprobación | agentes que pueden solicitarlo |
|---|---|---|---|
| `read_repo` | false | no, si fuente autorizada | Context/RAG, Implementación, Tests, Docs, QA, Seguridad |
| `read_db_metadata` | false | sí si BD real; no si dump autorizado | DB/Legacy, Context/RAG |
| `write_dry_run` | false | no si sandbox | Implementación, DB/Legacy |
| `write_artifacts` | true para artefactos internos | no | Spec, Docs, QA, DevOps |
| `write_files` | false | sí | ninguno por defecto |
| `run_tests` | false | no si sandbox y budget | Tests, Implementación |
| `external_api` | false | sí | ninguno por defecto |
| `deploy` | false | sí | DevOps solo planifica |
| `merge` | false | sí | ninguno |
| `read_secrets` | false | sí y se evita | ninguno por defecto |
| `write_memory` | false | sí con MemoryGate | ninguno directo |
| `cost_increase` | false | sí | Cost Optimizer vía approval request |
| `production_data` | false | sí | ninguno por defecto |

## 8. Schemas estrictos mínimos

### 8.1 `AgentOutput`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentOutput",
  "type": "object",
  "additionalProperties": false,
  "required": ["agent_id", "task_id", "status", "summary", "artifacts", "evidence", "issues", "next_action"],
  "properties": {
    "agent_id": { "type": "string" },
    "task_id": { "type": "string" },
    "status": { "type": "string", "enum": ["complete", "needs_user_input", "not_answerable", "error"] },
    "summary": { "type": "string" },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["artifact_id", "type", "hash"],
        "properties": {
          "artifact_id": { "type": "string" },
          "type": { "type": "string" },
          "path": { "type": "string" },
          "hash": { "type": "string" }
        }
      }
    },
    "evidence": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["evidence_id", "source_id", "chunk_id", "hash"],
        "properties": {
          "evidence_id": { "type": "string" },
          "source_id": { "type": "string" },
          "chunk_id": { "type": "string" },
          "hash": { "type": "string" }
        }
      }
    },
    "issues": { "type": "array", "items": { "type": "string" } },
    "next_action": { "type": "string", "enum": ["continue", "retry", "needs_user_input", "not_answerable", "error"] }
  }
}
```

### 8.2 `ToolResult`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ToolResult",
  "type": "object",
  "additionalProperties": false,
  "required": ["tool_id", "status", "input_hash", "output_hash", "side_effects", "sandbox", "latency_ms"],
  "properties": {
    "tool_id": { "type": "string" },
    "status": { "type": "string", "enum": ["success", "error", "blocked"] },
    "input_hash": { "type": "string" },
    "output_hash": { "type": "string" },
    "side_effects": { "type": "string", "enum": ["none", "read", "write", "external"] },
    "sandbox": { "type": "boolean" },
    "latency_ms": { "type": "integer", "minimum": 0 },
    "cache_hit": { "type": "boolean" },
    "source_ids": { "type": "array", "items": { "type": "string" } },
    "error_code": { "type": ["string", "null"] }
  }
}
```

### 8.3 `DryRunAction`

```json
{
  "action_id": "ACT-TBD",
  "mode": "dry_run",
  "risk": "low|medium|high|critical",
  "payload_preview": {},
  "required_approval": true,
  "rollback_plan": "TBD",
  "evidence_ids": []
}
```

### 8.4 `ApprovalRequest`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ApprovalRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["approval_id", "requested_action", "risk", "reason", "evidence_ids", "status"],
  "properties": {
    "approval_id": { "type": "string" },
    "requested_action": { "type": "string", "enum": ["write", "deploy", "merge", "external_api", "secrets", "infra", "cost_increase", "data_access"] },
    "risk": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
    "reason": { "type": "string" },
    "evidence_ids": { "type": "array", "items": { "type": "string" } },
    "status": { "type": "string", "enum": ["pending", "approved", "rejected"] }
  }
}
```

## 9. Política de memoria por agente

| agente | lee memoria | propone memoria | escribe memoria | TTL sugerido | notas |
|---|---|---|---|---|---|
| Orchestrator | factory/project aprobada | sí | no directo | run | Solo decisiones de flujo. |
| Spec | factory/project aprobada | sí | no directo | P30D | Requisitos recurrentes solo con evidencia. |
| Context/RAG | factory/project aprobada | sí | no directo | P7D | Nunca usa memoria para reemplazar evidencia actual. |
| Arquitectura | factory/project aprobada | sí | no directo | P30D | Patrones aprobados, no decisiones de negocio. |
| Documentación | factory/project aprobada | sí | no directo | P30D | Convenciones de docs aprobadas. |
| Tests | factory/project aprobada | sí | no directo | P30D | Estrategias de tests aprobadas. |
| Implementación | project aprobada mínima | sí | no directo | run/P7D | No recordar estilos no evidenciados. |
| OCR | ninguna por defecto | sí | no directo | run | OCR puede contaminarse; revisar. |
| API | factory/project aprobada | sí | no directo | P30D | Auth patterns aprobados. |
| QA | factory/project aprobada | sí | no directo | P30D | Checklists y defectos recurrentes. |
| Seguridad | factory/project aprobada | sí | no directo | P30D | Reglas de policy aprobadas. |
| DB/Legacy | project aprobada | sí | no directo | P7D | Esquemas obsoletos expiran rápido. |
| DevOps | factory/project aprobada | sí | no directo | P30D | SLOs/runbooks aprobados. |
| Cost Optimizer | logs agregados | sí | no directo | P30D | No guardar datos sensibles. |

## 10. Evals por agente

| agente | evals mínimos | condición de aprobación |
|---|---|---|
| Spec | E01, E02, E04, E05, E14 | Spec completa o fallback correcto. |
| Context/RAG | E03, E04, E05, E07, E10, E14 | Context-pack trazable y sin contaminación. |
| Arquitectura | E01, E04, E13, E14 | Plan mapea spec/constraints y no inventa. |
| Documentación | E01, E04, E07, E14 | Docs soportadas por evidencia y formato correcto. |
| Tests | E01, E09, E10, E14 | Plan/cobertura bloquean gaps. |
| Implementación | E06, E08, E10, E13 | No side effects, diff dry-run, policy respetada. |
| OCR | E04, E07, E10 | OCR con confidence y quarantine si aplica. |
| API | E01, E04, E07, E13 | OpenAPI válido, auth sin secretos. |
| QA | E01..E15 | Detecta fallas y usa estados cerrados. |
| Seguridad | E06, E07, E08, E13 | Bloquea acciones no permitidas. |
| DB/Legacy | E04, E05, E08, E10 | No DDL/DML, evidencia read-only. |
| DevOps | E08, E12, E15 | Logs/costos/aprobaciones completos. |
| Cost Optimizer | E12, E15 | Ledger exacto y degradación segura. |

## 11. Contrato de comunicación

- El orquestador nunca llama al LLM ni a tools directamente.
- Cada agente recibe solo `CycleState`, `context_pack`, memoria filtrada y tools allowlisted por ARNES.
- Cada agente devuelve `AgentOutput` validable.
- Las tools devuelven `ToolResult` validable.
- Si un agente necesita acción fuera de permiso, devuelve `ApprovalRequest`; no ejecuta.
- Si falta evidencia crítica, devuelve `not_answerable`.
- Si falta dato crítico del usuario, devuelve `needs_user_input`.
- Si hay error de tool/schema/policy no reparable, devuelve `error`.

## 12. Checklist operativo de agentes

- [x] Agente de documentación técnica detallado.
- [x] Agente de tests para planes y ejecución con cobertura.
- [x] Agente de especificación detallada.
- [x] Agente de implementación con documentación en código.
- [x] Agente OCR para análisis de imágenes.
- [x] Agente de generación de APIs seguras con tokens y ejemplos.
- [x] Agente QA con checklist práctico.
- [x] Agentes adicionales justificados por permisos/riesgo: Context/RAG, Arquitectura, Seguridad, DB/Legacy, DevOps/Observabilidad, Cost Optimizer.
- [x] Tools determinísticas allowlisted.
- [x] Permisos prohibidos por defecto.
- [x] Schemas estrictos definidos.
- [x] Evals por agente definidos.


## 13. Trazabilidad de agentes, skills y tools

| elemento | debe mapear a | evidencia mínima |
|---|---|---|
| `agent_id` | `task_id`, `gate_id`, `budget` | AgentSpec versionado y log de ejecución |
| `skill_id` | `agent_id`, `tool_id`, `schema_id` | SkillSpec y tests contract/permission/adversarial |
| `tool_id` | `permission`, `side_effects`, `output_schema` | ToolSpec, input_hash, output_hash y tool-log |
| `AgentOutput` | `spec_id`, `task_id`, `evidence_id`, `test_id` | ValidationReport |
| `ApprovalRequest` | acción sensible, riesgo, rollback | approval_id y evidencia |

La salida de cualquier agente debe usar los estados cerrados `complete`, `needs_user_input`, `not_answerable` o `error`. Ningún agente invoca a otro agente ni a una tool por fuera del harness; toda ejecución autorizada se realiza mediante `harness.run_agent(agent_id, state)` desde el orquestador.
