# Constitution

## Objetivo
Implementar fabrica agéntica ARNES/SDD operativa, deterministica y lista para proyectos independientes.

## Reglas no negociables
- no_inventar=true
- dry_run=true
- read_only_por_defecto=true
- puerta_unica=harness.run_agent(agent_id, state)
- estados_cerrados=complete|needs_user_input|not_answerable|error

## Fuente
work_order_id=WO-FACTORY-BOOTSTRAP
