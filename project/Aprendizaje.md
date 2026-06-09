# Aprendizaje

## Reglas
- Este archivo guarda propuestas validadas, no aprendizaje automatico.
- Ninguna propuesta se activa sin aprobacion.
- Toda entrada requiere evidencia, TTL, confianza, scope y rollback.
- La memoria factory y la memoria de proyecto se registran en ledgers separados.
- La memoria tainted/suspect se manda a cuarentena y no entra al contexto.

## Propuestas pendientes
| id | fecha | scope | aprendizaje | evidencia | confianza | TTL | riesgo | taint | estado |
|---|---|---|---|---|---:|---|---|---|---|

## Aprobadas
| id | fecha | scope | contenido | fuente | confidence | TTL | rollback |
|---|---|---|---|---|---:|---|---|

## Rechazadas
| id | fecha | razon | riesgo | fuente |
|---|---|---|---|---|

## Expiradas
| id | fecha_expiracion | accion | rollback |
|---|---|---|---|

## Conflictos
| id | memoria A | memoria B | fuente nueva | resolucion |
|---|---|---|---|---|
