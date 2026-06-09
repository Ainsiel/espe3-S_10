# RUNBOOK

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
