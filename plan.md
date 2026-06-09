# Plan

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
