# Fabrica FULL TRES

Indice operativo para continuar en un hilo limpio.

## Estado
- status: complete
- checklist: complete / approved / L5
- tests: 23 OK
- verify: `python3 scripts/verify_factory.py` => complete
- fecha de cierre: 2026-06-08

## Entrada recomendada
Leer primero:
1. `NUEVO_HILO.md`
2. `RUN_STATE.md`
3. `reports/checklist-audit.json`
4. `traceability-matrix.md`
5. `PRACTICAS_PERMANENTES.md`
6. `DESIGN_SYSTEM.md`
7. `PRICING.md`

## Contrato congelado
- fases SDD: 22 pasos de flujo sobre 17 fases nominales
- agentes: 17
- skills: 27
- tools: 39
- gates: 27
- validators: 10
- consumo por ciclo: cada `AgentOutput` expone `usage_estimate.input_tokens` y `usage_estimate.output_tokens`

## Modulos ejecutables
- `fabrica/`: arnes, agentes, registries, tools, validators, memoria, pricing, frontend y auditoria.
- `scripts/verify_factory.py`: verificacion integral.
- `tests/test_factory.py`: pruebas unitarias de completitud y comportamiento.
- `project/`: carpeta reservada para proyectos independientes.

## Artefactos que no son ruido
No borrar estos grupos sin una razon trazable:
- `agent-logs/`
- `tool-logs/`
- `reports/`
- `.fabrica/`
- `billing-ledger.json`
- `pricing-catalog.json`
- `state.json`
- `validation-report.json`
- `final-report.json`

## Verificacion
```bash
python3 -m unittest discover -s tests
python3 scripts/verify_factory.py
```

## Siguiente paso
Esperar un proyecto independiente dentro de `project/`, crear su `work_order` antes de implementar y reportar input/output tokens despues de cada ciclo.
