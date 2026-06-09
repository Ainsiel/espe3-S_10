# Nuevo hilo limpio

Este archivo es el resumen corto. El handoff principal es `HANDOFF.md`; el nuevo hilo debe leer ambos antes de operar.

## Contexto minimo
Workspace:
`/Volumes/KINGSTON/CODEX HD/Fabrica FULL TRES`

La fabrica ARNES/SDD ya esta implementada, verificada y lista para operar proyectos independientes dentro de `project/`. No reiniciar desde cero.

## Estado certificado
- `python3 -m unittest discover -s tests`: 23 tests OK.
- `python3 scripts/verify_factory.py`: `factory_verify_status=complete`.
- Checklist aplicado: `status=complete`, `decision=approved`, `maturity_level=L5`.
- Evals: 4/4 pass.
- Costo externo del bootstrap: 0 USD, modo local deterministico sin LLM.

## Capacidades ya incorporadas
- Arnes/Harness como puerta unica.
- Orquestador SDD con 17 fases.
- AgentRegistry con 17 agentes.
- SkillRegistry con 27 skills.
- ToolRegistry allowlist con 39 tools.
- ValidatorChain con 10 validators, incluido `FrontendQualityValidator`.
- Memoria factory/project separada con `Aprendizaje.md`, `HANDOFF.md`, ledgers independientes y cuarentena por proyecto.
- Billing real de tokens por usage API cuando exista modelo oficial y usage.
- Estimacion obligatoria de tokens input/output despues de cada ciclo via `usage_estimate` y `billing-ledger.json`.
- Frontend moderno como contrato permanente: design tokens, UX/a11y, responsive, QA visual y copy.
- Buenas practicas permanentes incorporadas desde `buenas_practicas.md`.

## Reglas permanentes
- Full determinismo: temperatura 0, sin variabilidad y sin decisiones por intuicion.
- No inventar: si falta evidencia, devolver `not_answerable` o pedir input.
- Contexto minimo: usar index, cache, tags y artefactos resumidos.
- No mezclar memorias entre proyectos.
- Toda ejecucion pasa por `HarnessRunner.run_agent`.
- Despues de cada ciclo, reportar input/output tokens estimados. Formato minimo: `input_tokens=<n>`, `output_tokens=<n>`, `usage_source=<api_usage|local_estimate>`.
- Toda salida importante requiere evidencia, QA, logs, trazabilidad y checklist.
- Frontend por defecto: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui y lucide-react cuando el proyecto lo autorice.
- Accesibilidad: contraste WCAG AA, foco visible, responsive mobile-first, estados loading/empty/data/permission/error/success.

## Documentos clave
- `README.md`: indice operativo.
- `HANDOFF.md`: entrada canonica para hilo limpio.
- `RUN_STATE.md`: estado del ultimo cierre.
- `reports/checklist-audit.json`: auditoria final.
- `traceability-matrix.md`: trazabilidad de requisitos.
- `PRACTICAS_PERMANENTES.md`: buenas practicas obligatorias.
- `DESIGN_SYSTEM.md`: contrato visual frontend.
- `frontend-quality-contract.json`: contrato frontend auditable por maquina.
- `PRICING.md`: facturacion real de tokens y reglas de no respuesta si falta tarifa oficial.
- `billing-ledger.json`: ledger detallado.
- `agent-registry.json`, `skill-registry.json`, `tool-registry.json`: registros congelados.

## Comandos de salud
```bash
python3 -m unittest discover -s tests
python3 scripts/verify_factory.py
```

## Nuevo proyecto independiente
Cuando el usuario entregue un proyecto nuevo:
1. Crear carpeta bajo `project/<nombre_proyecto>`.
2. Crear o normalizar `work_order.json` del proyecto.
3. Inicializar memoria independiente en `project/<nombre_proyecto>/.fabrica/memory/project/`.
4. Ejecutar el ciclo por harness, no por llamadas directas a tools/agentes.
5. Generar QA, trazabilidad, logs, ledger y reporte final del proyecto.
6. En cada cierre de ciclo y en el cierre final, entregar estimacion de tokens de entrada y salida.

## Mensaje sugerido para arrancar el hilo nuevo
```text
Estamos en /Volumes/KINGSTON/CODEX HD/Fabrica FULL TRES. Lee HANDOFF.md, NUEVO_HILO.md y README.md. La fabrica ya esta verificada; no reinicies desde cero. Usa solo arnes/harness, memoria separada por proyecto y cuarentena cualquier contexto tainted antes de continuar.
```
