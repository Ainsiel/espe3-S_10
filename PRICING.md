# Facturacion real de tokens

## Fuente

- Pricing source: https://developers.openai.com/api/docs/pricing
- Reasoning source: https://platform.openai.com/docs/guides/reasoning
- pricing_version: `openai-pricing-2026-06-08`

## Regla ARNES

La fabrica no inventa costos. El ledger usa tres modos:

| modo | uso | resultado |
|---|---|---|
| `api_usage` | Usage real entregado por Responses, Chat Completions u Organization Usage API. | Calcula costo con tarifa oficial versionada. |
| `local_estimate` | Ejecucion local sin llamada LLM. | Registra tokens estimados para presupuesto, costo externo `0`. |
| `missing_official_rate` | Modelo/tier sin tarifa oficial registrada. | `not_answerable`; no calcula costo. |

## Formula

```text
billable_input_tokens = input_tokens - cached_input_tokens
visible_output_tokens = output_tokens - reasoning_tokens

total_usd =
  billable_input_tokens / 1_000_000 * input_rate
+ cached_input_tokens / 1_000_000 * cached_input_rate
+ output_tokens / 1_000_000 * output_rate
+ tool_call_charges
+ regional_uplift_si_aplica
```

Los `reasoning_tokens` se registran por separado para auditoria, pero se cobran dentro de `output_tokens`.

## Artefactos

- `pricing-catalog.json`: snapshot de tarifas oficiales usadas por el run.
- `billing-ledger.json`: detalle por fase/agente/modelo/usage/costo.
- `cost-report.json`: resumen de estrategia, fuente de pricing y estado.

## Entrega por ciclo

Despues de cada ciclo/agente, la fabrica debe entregar una estimacion visible de consumo:

```text
input_tokens=<n>
output_tokens=<n>
usage_source=<api_usage|local_estimate|missing_official_rate>
```

La fuente tecnica es `AgentOutput.usage_estimate` y se sincroniza con la entrada correspondiente de `billing-ledger.json`.
