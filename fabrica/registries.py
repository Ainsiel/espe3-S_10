"""Registros versionados de agentes, skills y tools."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .constants import AGENT_IDS, MODEL_SNAPSHOT, SKILL_IDS, TOOL_IDS
from .schemas import AgentSpec, Budget, SkillSpec, ToolSpec


def _budget(input_tokens: int, output_tokens: int, tool_calls: int, timeout_ms: int) -> Budget:
    return Budget(
        max_input_tokens=input_tokens,
        max_output_tokens=output_tokens,
        max_tool_calls=tool_calls,
        max_latency_ms=timeout_ms,
        max_cost_usd=0,
    )


def _model_policy() -> dict[str, Any]:
    return {
        "model": MODEL_SNAPSHOT,
        "temperature": 0,
        "top_p": 1,
        "seed": 12345,
        "parallel_tool_calls": False,
        "response_format": "strict_json_schema",
    }


class AgentRegistry:
    def __init__(self) -> None:
        self._agents = self._build()

    def _agent(
        self,
        agent_id: str,
        name: str,
        purpose: str,
        responsibility: str,
        tools: tuple[str, ...],
        permissions: dict[str, bool],
        gates: tuple[str, ...],
        budget: Budget,
        evals: tuple[str, ...],
        inputs: tuple[str, ...] = ("CycleState", "context_pack", "memory_pack"),
        outputs: tuple[str, ...] = ("AgentOutput",),
    ) -> AgentSpec:
        return AgentSpec(
            agent_id=agent_id,
            agent_name=name,
            version="1.0.0",
            status="approved",
            purpose=purpose,
            single_responsibility=responsibility,
            use_when=(purpose,),
            do_not_use_when=("Falta evidencia critica o permiso requerido.",),
            inputs=inputs,
            outputs=outputs,
            allowed_tools=tools,
            permissions=permissions,
            gates=gates,
            budget=budget,
            memory_read_scopes=("factory", "project"),
            write_memory=False,
            evals=evals,
            model_policy=_model_policy(),
        )

    def _build(self) -> dict[str, AgentSpec]:
        read_artifact = {"read_repo": True, "write_artifacts": True, "run_tests": False, "external_api": False, "deploy": False, "read_secrets": False}
        return {
            "agent.orchestrator": self._agent(
                "agent.orchestrator",
                "Orquestador de flujo",
                "Coordinar transiciones SDD sin ejecutar trabajo tecnico directo.",
                "Flujo solamente.",
                tuple(),
                {"flow_only": True, "write_artifacts": False, "read_secrets": False},
                ("policy", "budget"),
                _budget(4000, 1000, 0, 10000),
                ("E01", "E14"),
            ),
            "agent.spec": self._agent(
                "agent.spec",
                "Agente de especificacion detallada",
                "Definir constitution, spec, aclaraciones, checklist y tasks trazables.",
                "Gobierno de requisitos SDD.",
                ("tool.schema.validate", "tool.docs.render", "tool.traceability.check", "tool.hash.compute"),
                {"write_artifacts": True, "read_repo": False, "read_secrets": False},
                ("schema", "spec", "clarification", "evidence", "budget"),
                _budget(12000, 3000, 3, 30000),
                ("E01", "E02", "E04", "E14"),
            ),
            "agent.context_rag": self._agent(
                "agent.context_rag",
                "Agente Context/RAG",
                "Recuperar evidencia minima de fuentes autorizadas con indice/cache.",
                "Evidencia y context-pack.",
                ("tool.index.query", "tool.cache.get", "tool.cache.set", "tool.code.search", "tool.db.metadata_readonly", "tool.context.compact"),
                {"read_repo": True, "read_db_metadata": False, "write_artifacts": True, "read_secrets": False},
                ("context", "evidence", "safety", "budget"),
                _budget(10000, 3000, 4, 30000),
                ("E03", "E04", "E05", "E07", "E10", "E14"),
            ),
            "agent.architecture_plan": self._agent(
                "agent.architecture_plan",
                "Agente Arquitectura/Plan",
                "Crear plan tecnico, riesgos y migracion incremental desde spec y evidencia.",
                "Planificacion arquitectonica.",
                ("tool.docs.render", "tool.openapi.validate", "tool.dependency.scan", "tool.traceability.check"),
                read_artifact,
                ("plan", "plan_validation", "evidence", "budget"),
                _budget(14000, 4000, 3, 45000),
                ("E01", "E04", "E13", "E14"),
            ),
            "agent.documentation": self._agent(
                "agent.documentation",
                "Agente Documentacion",
                "Generar documentacion tecnica, handoff y docs de mantenimiento.",
                "Documentacion verificable.",
                ("tool.docs.render", "tool.diff.dry_run", "tool.schema.validate", "tool.traceability.check"),
                read_artifact,
                ("schema", "evidence", "consistency", "documentation", "final_format"),
                _budget(10000, 4000, 2, 30000),
                ("E01", "E04", "E07", "E14"),
            ),
            "agent.tests_coverage": self._agent(
                "agent.tests_coverage",
                "Agente Tests/Cobertura",
                "Crear plan de pruebas, ejecutar suites sandbox y validar cobertura.",
                "Calidad verificable por pruebas.",
                ("tool.test.run_sandbox", "tool.coverage.report", "tool.mutation.run_dry", "tool.openapi.validate", "tool.traceability.check"),
                {"read_repo": True, "write_artifacts": True, "run_tests": True, "read_secrets": False},
                ("tests", "coverage", "schema", "budget", "sandbox"),
                _budget(8000, 2000, 4, 120000),
                ("E01", "E09", "E10", "E14"),
            ),
            "agent.implementation": self._agent(
                "agent.implementation",
                "Agente Implementacion",
                "Producir diff dry-run segun tasks aprobadas y documentacion de codigo.",
                "Ejecucion tecnica acotada.",
                ("tool.code.search", "tool.ast.parse", "tool.diff.dry_run", "tool.test.run_sandbox", "tool.schema.validate"),
                {"read_repo": True, "write_dry_run": True, "run_tests": True, "read_secrets": False},
                ("schema", "policy", "sandbox", "tests", "coverage", "security"),
                _budget(16000, 5000, 4, 120000),
                ("E06", "E08", "E10", "E13"),
            ),
            "agent.ocr_image": self._agent(
                "agent.ocr_image",
                "Agente OCR Imagen",
                "Extraer texto y layout de imagenes autorizadas.",
                "Evidencia visual estructurada.",
                ("tool.ocr.extract", "tool.image.layout", "tool.safety.scan_text"),
                {"read_images": True, "write_artifacts": True, "read_secrets": False},
                ("schema", "safety", "evidence", "policy"),
                _budget(4000, 2000, 3, 30000),
                ("E04", "E07", "E10"),
            ),
            "agent.api_secure": self._agent(
                "agent.api_secure",
                "Agente API segura",
                "Diseñar contratos API seguros con tokens, ejemplos y tests.",
                "Contratos API y autorizacion.",
                ("tool.openapi.validate", "tool.schema.validate", "tool.secrets.scan", "tool.docs.render"),
                read_artifact,
                ("schema", "contract", "security", "tests", "evidence"),
                _budget(10000, 3000, 3, 30000),
                ("E01", "E04", "E07", "E13"),
            ),
            "agent.qa": self._agent(
                "agent.qa",
                "Agente QA",
                "Validar consistencia, cobertura, checklist y cierre.",
                "Aprobar o bloquear con issues concretos.",
                ("tool.validator.chain", "tool.traceability.check", "tool.schema.validate"),
                {"approve_block": True, "write_artifacts": True, "read_repo": True, "read_secrets": False},
                ("schema", "evidence", "consistency", "coverage", "budget", "final_format"),
                _budget(12000, 3000, 3, 30000),
                ("E01", "E02", "E03", "E04", "E05", "E12", "E14"),
            ),
            "agent.security_policy": self._agent(
                "agent.security_policy",
                "Agente Seguridad/Policy",
                "Revisar permisos, secretos, dependencias y prompt injection.",
                "Bloqueo de riesgos de seguridad.",
                ("tool.secrets.scan", "tool.dependency.scan", "tool.sast.scan", "tool.policy.evaluate", "tool.safety.scan_text"),
                {"approve_block": True, "write_artifacts": True, "read_repo": True, "read_secrets": False},
                ("security", "secrets", "dependency", "policy"),
                _budget(10000, 3000, 4, 60000),
                ("E06", "E07", "E08", "E13"),
            ),
            "agent.db_legacy": self._agent(
                "agent.db_legacy",
                "Agente DB/Legacy",
                "Analizar SQL, metadata, stored procedures, triggers, views y migracion.",
                "Inventario e impacto BD read-only.",
                ("tool.sql.parse", "tool.db.metadata_readonly", "tool.schema.diff_dry_run"),
                {"read_db_metadata": True, "write_dry_run": True, "read_secrets": False},
                ("context", "sandbox", "safety"),
                _budget(9000, 2500, 3, 60000),
                ("E04", "E05", "E08", "E10"),
            ),
            "agent.frontend_design_system": self._agent(
                "agent.frontend_design_system",
                "Agente Frontend Design System",
                "Definir tokens, componentes, paleta, tipografia y contrato visual permanente.",
                "Sistema visual moderno medible.",
                (
                    "tool.frontend.design_tokens.validate",
                    "tool.frontend.component_inventory",
                    "tool.docs.render",
                    "tool.traceability.check",
                ),
                read_artifact,
                ("design_system", "frontend_quality", "accessibility", "responsive", "evidence", "budget"),
                _budget(10000, 3000, 4, 30000),
                ("E01", "E04", "E14", "E16"),
            ),
            "agent.ux_accessibility": self._agent(
                "agent.ux_accessibility",
                "Agente UX/Accesibilidad",
                "Validar UX, copy, contraste, estados de pantalla y responsive mobile-first.",
                "Ergonomia, accesibilidad y claridad de interfaz.",
                (
                    "tool.frontend.contrast.audit",
                    "tool.frontend.responsive.check",
                    "tool.frontend.copy_lint",
                    "tool.docs.render",
                    "tool.traceability.check",
                ),
                read_artifact,
                ("ux", "accessibility", "responsive", "frontend_quality", "evidence", "budget"),
                _budget(10000, 3000, 5, 30000),
                ("E01", "E04", "E14", "E16"),
            ),
            "agent.frontend_visual_qa": self._agent(
                "agent.frontend_visual_qa",
                "Agente Frontend Visual QA",
                "Cerrar QA visual, responsive, estados y contrato frontend antes de deploy.",
                "Verificacion visual y a11y final.",
                (
                    "tool.frontend.visual_report",
                    "tool.frontend.contrast.audit",
                    "tool.frontend.responsive.check",
                    "tool.validator.chain",
                    "tool.traceability.check",
                ),
                {"approve_block": True, "write_artifacts": True, "read_repo": True, "read_secrets": False},
                ("visual_qa", "frontend_quality", "accessibility", "responsive", "coverage", "budget"),
                _budget(10000, 3000, 5, 30000),
                ("E01", "E04", "E14", "E16"),
            ),
            "agent.devops_observability": self._agent(
                "agent.devops_observability",
                "Agente DevOps/Observabilidad",
                "Definir CI/CD dry-run, logs, SLOs, dashboards y handoff operativo.",
                "Operacion y despliegue sin side effects reales.",
                ("tool.log.write", "tool.metrics.emit", "tool.ci.validate_dry_run", "tool.billing.compute"),
                {"write_artifacts": True, "dry_run": True, "deploy": False, "read_secrets": False},
                ("observability", "budget", "human_approval"),
                _budget(8000, 2500, 4, 60000),
                ("E08", "E12", "E15"),
            ),
            "agent.cost_optimizer": self._agent(
                "agent.cost_optimizer",
                "Agente Cost Optimizer",
                "Optimizar tokens, tool calls, cache, latencia y budget.",
                "Control de costo y eficiencia.",
                ("tool.billing.compute", "tool.cache.get", "tool.trace.analyze"),
                {"read_logs": True, "write_artifacts": True, "read_secrets": False},
                ("budget", "observability"),
                _budget(6000, 1500, 3, 15000),
                ("E12", "E15"),
            ),
        }

    def get(self, agent_id: str) -> AgentSpec:
        if agent_id not in self._agents:
            raise KeyError(agent_id)
        return self._agents[agent_id]

    def all(self) -> dict[str, AgentSpec]:
        return dict(self._agents)

    def as_json(self) -> dict[str, Any]:
        return {agent_id: spec.to_dict() for agent_id, spec in self._agents.items()}

    def verify_complete(self) -> bool:
        return set(self._agents) == set(AGENT_IDS)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools = self._build()

    def _tool(
        self,
        tool_id: str,
        purpose: str,
        permissions: tuple[str, ...],
        side_effects: str,
        timeout_ms: int = 10000,
        retries: int = 1,
        cost: str = "low",
        sandbox: bool = True,
        errors: tuple[str, ...] = ("tool_error",),
        approval_required: bool = False,
    ) -> ToolSpec:
        schema_name = "".join(part.title() for part in tool_id.split(".")[1:])
        return ToolSpec(
            tool_id=tool_id,
            purpose=purpose,
            input_schema=schema_name + "Input",
            output_schema=schema_name + "Output",
            error_schema=schema_name + "Error",
            permissions=permissions,
            timeout_ms=timeout_ms,
            retries=retries,
            cost=cost,
            side_effects=side_effects,
            sandbox=sandbox,
            errors=errors,
            approval_required=approval_required,
        )

    def _build(self) -> dict[str, ToolSpec]:
        specs = [
            self._tool("tool.file.read", "Leer archivos autorizados.", ("read_repo",), "read"),
            self._tool("tool.hash.compute", "Calcular sha256.", ("read_repo",), "none", retries=0, cost="free"),
            self._tool("tool.index.build", "Crear indice interno.", ("write_artifacts",), "write", 120000),
            self._tool("tool.index.query", "Consultar indice.", ("read_repo",), "read", 15000),
            self._tool("tool.cache.get", "Leer cache.", ("read_logs",), "read", 1000, 0, "free"),
            self._tool("tool.cache.set", "Escribir cache interna.", ("write_artifacts",), "write", 1000, 0, "free"),
            self._tool("tool.context.compact", "Compactar contexto.", ("read_repo",), "none", 5000),
            self._tool("tool.code.search", "Buscar codigo/texto.", ("read_repo",), "read"),
            self._tool("tool.ast.parse", "Parsear codigo.", ("read_repo",), "read"),
            self._tool("tool.sql.parse", "Parsear SQL.", ("read_db_metadata",), "read"),
            self._tool("tool.db.metadata_readonly", "Leer metadata BD autorizada.", ("read_db_metadata",), "read", 30000),
            self._tool("tool.schema.diff_dry_run", "Simular diff de esquema.", ("write_dry_run",), "none", 60000),
            self._tool("tool.diff.dry_run", "Generar patch preview.", ("write_dry_run",), "none", 30000),
            self._tool("tool.test.run_sandbox", "Ejecutar tests sandbox.", ("run_tests",), "none", 120000),
            self._tool("tool.coverage.report", "Leer cobertura.", ("read_repo",), "read", retries=0),
            self._tool("tool.mutation.run_dry", "Mutation testing dry-run.", ("run_tests",), "none", 300000, 0, "high"),
            self._tool("tool.openapi.validate", "Validar OpenAPI.", ("write_artifacts",), "none"),
            self._tool("tool.schema.validate", "Validar schemas estrictos.", ("write_artifacts",), "none"),
            self._tool("tool.docs.render", "Renderizar docs.", ("write_artifacts",), "write"),
            self._tool("tool.validator.chain", "Ejecutar validadores.", ("approve_block",), "none", 15000),
            self._tool("tool.traceability.check", "Verificar trazabilidad.", ("write_artifacts",), "none"),
            self._tool("tool.policy.evaluate", "Evaluar policy.", ("approve_block",), "none", 5000, 0),
            self._tool("tool.secrets.scan", "Escanear secretos.", ("read_repo",), "read", 30000),
            self._tool("tool.dependency.scan", "Analizar dependencias.", ("read_repo",), "read", 60000),
            self._tool("tool.sast.scan", "Analisis estatico.", ("read_repo",), "read", 60000),
            self._tool("tool.ocr.extract", "OCR autorizado.", ("read_images",), "read", 30000),
            self._tool("tool.image.layout", "Extraer layout visual.", ("read_images",), "read", 30000),
            self._tool("tool.safety.scan_text", "Detectar prompt injection/PII.", ("read_repo",), "none"),
            self._tool("tool.ci.validate_dry_run", "Validar CI sin deploy.", ("dry_run",), "none", 120000),
            self._tool("tool.log.write", "Escribir logs internos.", ("write_artifacts",), "write", 1000, cost="free"),
            self._tool("tool.metrics.emit", "Emitir metricas internas.", ("write_artifacts",), "write", 1000, 0),
            self._tool("tool.billing.compute", "Calcular ledger.", ("read_logs",), "none", 5000, 0),
            self._tool("tool.frontend.design_tokens.validate", "Validar tokens de diseno frontend.", ("write_artifacts",), "none", 10000, 0),
            self._tool("tool.frontend.contrast.audit", "Auditar contraste WCAG de tokens frontend.", ("write_artifacts",), "none", 10000, 0),
            self._tool("tool.frontend.responsive.check", "Generar matriz responsive mobile-first.", ("write_artifacts",), "none", 10000, 0),
            self._tool("tool.frontend.component_inventory", "Inventariar componentes UI obligatorios.", ("write_artifacts",), "none", 10000, 0),
            self._tool("tool.frontend.copy_lint", "Validar copy accionable y no ambiguo.", ("write_artifacts",), "none", 10000, 0),
            self._tool("tool.frontend.visual_report", "Generar reporte QA visual frontend.", ("write_artifacts",), "none", 10000, 0),
            self._tool("tool.trace.analyze", "Analizar trazas.", ("read_logs",), "read", retries=0),
        ]
        return {spec.tool_id: spec for spec in specs}

    def get(self, tool_id: str) -> ToolSpec:
        if tool_id not in self._tools:
            raise KeyError(tool_id)
        return self._tools[tool_id]

    def all(self) -> dict[str, ToolSpec]:
        return dict(self._tools)

    def as_json(self) -> dict[str, Any]:
        return {tool_id: spec.to_dict() for tool_id, spec in self._tools.items()}

    def verify_complete(self) -> bool:
        return set(self._tools) == set(TOOL_IDS)


class SkillRegistry:
    def __init__(self) -> None:
        self._skills = self._build()

    def _build(self) -> dict[str, SkillSpec]:
        rows = [
            ("skill.work_order.normalize", "validate", "Normalizar input a WorkOrder.", "tool.schema.validate", False),
            ("skill.source.hash", "compute", "Calcular hashes de fuentes.", "tool.hash.compute", True),
            ("skill.rag.retrieve_context", "retrieval", "Recuperar context-pack minimo.", "tool.index.query", True),
            ("skill.cache.lookup", "compute", "Consultar cache.", "tool.cache.get", True),
            ("skill.cache.store", "compute", "Guardar resultado cacheable.", "tool.cache.set", True),
            ("skill.context.compact", "compute", "Compactar contexto conservando evidencia.", "tool.context.compact", True),
            ("skill.code.search_symbols", "retrieval", "Buscar simbolos y rutas.", "tool.code.search", True),
            ("skill.ast.parse", "compute", "Parsear codigo.", "tool.ast.parse", True),
            ("skill.sql.parse", "compute", "Parsear SQL.", "tool.sql.parse", True),
            ("skill.db.introspect_readonly", "retrieval", "Extraer metadata BD.", "tool.db.metadata_readonly", True),
            ("skill.openapi.validate", "validate", "Validar OpenAPI.", "tool.openapi.validate", True),
            ("skill.test.plan_coverage", "compute", "Mapear requisitos a pruebas.", "tool.traceability.check", True),
            ("skill.test.run_sandbox", "test", "Ejecutar tests autorizados.", "tool.test.run_sandbox", True),
            ("skill.coverage.read", "validate", "Leer cobertura.", "tool.coverage.report", True),
            ("skill.security.scan", "validate", "Escanear secretos, deps y SAST.", "tool.secrets.scan", True),
            ("skill.ocr.extract", "retrieval", "Extraer texto de imagen.", "tool.ocr.extract", True),
            ("skill.docs.render", "file_write_dry_run", "Renderizar docs.", "tool.docs.render", True),
            ("skill.diff.generate_dry_run", "file_write_dry_run", "Producir patch sin aplicar.", "tool.diff.dry_run", False),
            ("skill.billing.compute", "observe", "Calcular costos y latencia.", "tool.billing.compute", True),
            ("skill.billing.normalize_usage", "observe", "Normalizar usage API real a ledger facturable.", "tool.billing.compute", True),
            ("skill.frontend.design_tokens_validate", "validate", "Validar tokens visuales permanentes.", "tool.frontend.design_tokens.validate", True),
            ("skill.frontend.contrast_audit", "validate", "Auditar contraste WCAG AA.", "tool.frontend.contrast.audit", True),
            ("skill.frontend.responsive_matrix", "validate", "Construir matriz responsive mobile-first.", "tool.frontend.responsive.check", True),
            ("skill.frontend.component_inventory", "compute", "Registrar componentes UI esperados.", "tool.frontend.component_inventory", True),
            ("skill.frontend.copy_lint", "validate", "Detectar copy ambiguo o poco accionable.", "tool.frontend.copy_lint", True),
            ("skill.frontend.visual_report", "validate", "Consolidar QA visual frontend.", "tool.frontend.visual_report", True),
            ("skill.validator.chain", "validate", "Ejecutar ValidatorChain.", "tool.validator.chain", False),
        ]
        skills: dict[str, SkillSpec] = {}
        for skill_id, kind, purpose, tool_id, cache in rows:
            skills[skill_id] = SkillSpec(
                skill_id=skill_id,
                kind=kind,
                purpose=purpose,
                tool_id=tool_id,
                input_schema=skill_id.split(".", 1)[1].replace(".", "_") + "_input",
                output_schema=skill_id.split(".", 1)[1].replace(".", "_") + "_output",
                deterministic=True,
                timeout_ms=30000,
                retry=1,
                cache=cache,
            )
        return skills

    def all(self) -> dict[str, SkillSpec]:
        return dict(self._skills)

    def as_json(self) -> dict[str, Any]:
        return {skill_id: asdict(spec) for skill_id, spec in self._skills.items()}

    def verify_complete(self) -> bool:
        return set(self._skills) == set(SKILL_IDS)
