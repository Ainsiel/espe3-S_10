"""Catalogo oficial de precios y facturacion real por tokens.

Los costos se calculan solo con uso real reportado por API o con tarifas
oficiales versionadas. Si falta precio para un modelo no-local, el resultado
queda `not_answerable` y no inventa costo.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


PRICING_VERSION = "openai-pricing-2026-06-08"
PRICING_SOURCE_URL = "https://developers.openai.com/api/docs/pricing"
REASONING_SOURCE_URL = "https://platform.openai.com/docs/guides/reasoning"
USD_PER_MILLION = Decimal("1000000")


@dataclass(frozen=True)
class ModelRate:
    model: str
    service_tier: str
    context: str
    input_per_1m: Decimal | None
    cached_input_per_1m: Decimal | None
    output_per_1m: Decimal | None
    source: str = PRICING_SOURCE_URL

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("input_per_1m", "cached_input_per_1m", "output_per_1m"):
            data[key] = None if data[key] is None else str(data[key])
        return data


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    usage_source: str = "api_usage"

    @property
    def billable_input_tokens(self) -> int:
        return max(0, self.input_tokens - self.cached_input_tokens)

    @property
    def visible_output_tokens(self) -> int:
        return max(0, self.output_tokens - self.reasoning_tokens)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["billable_input_tokens"] = self.billable_input_tokens
        data["visible_output_tokens"] = self.visible_output_tokens
        return data


class PricingCatalog:
    def __init__(self) -> None:
        self._rates = self._build_rates()

    def _build_rates(self) -> dict[tuple[str, str, str], ModelRate]:
        rows: list[ModelRate] = []

        def add(model: str, tier: str, context: str, input_rate: str | None, cached_rate: str | None, output_rate: str | None) -> None:
            rows.append(
                ModelRate(
                    model=model,
                    service_tier=tier,
                    context=context,
                    input_per_1m=None if input_rate is None else Decimal(input_rate),
                    cached_input_per_1m=None if cached_rate is None else Decimal(cached_rate),
                    output_per_1m=None if output_rate is None else Decimal(output_rate),
                )
            )

        # Flagship models, Standard tier. Prices per 1M tokens.
        add("gpt-5.5", "standard", "short", "5.00", "0.50", "30.00")
        add("gpt-5.5", "standard", "long", "10.00", "1.00", "45.00")
        add("gpt-5.5-pro", "standard", "short", "30.00", None, "180.00")
        add("gpt-5.5-pro", "standard", "long", "60.00", None, "270.00")
        add("gpt-5.4", "standard", "short", "2.50", "0.25", "15.00")
        add("gpt-5.4", "standard", "long", "5.00", "0.50", "22.50")
        add("gpt-5.4-mini", "standard", "short", "0.75", "0.075", "4.50")
        add("gpt-5.4-nano", "standard", "short", "0.20", "0.02", "1.25")
        add("gpt-5.4-pro", "standard", "short", "30.00", None, "180.00")
        add("gpt-5.4-pro", "standard", "long", "60.00", None, "270.00")

        # Batch and Flex are 50% lower on the official page for this table.
        add("gpt-5.5", "batch", "short", "2.50", "0.25", "15.00")
        add("gpt-5.5", "batch", "long", "5.00", "0.50", "22.50")
        add("gpt-5.4", "batch", "short", "1.25", "0.13", "7.50")
        add("gpt-5.4", "batch", "long", "2.50", "0.25", "11.25")
        add("gpt-5.4-mini", "batch", "short", "0.375", "0.0375", "2.25")
        add("gpt-5.4-nano", "batch", "short", "0.10", "0.01", "0.625")
        add("gpt-5.4-pro", "batch", "short", "15.00", None, "90.00")
        add("gpt-5.4-pro", "batch", "long", "30.00", None, "135.00")
        add("gpt-5.5", "flex", "short", "2.50", "0.25", "15.00")
        add("gpt-5.5", "flex", "long", "5.00", "0.50", "22.50")
        add("gpt-5.4", "flex", "short", "1.25", "0.13", "7.50")
        add("gpt-5.4", "flex", "long", "2.50", "0.25", "11.25")
        add("gpt-5.4-mini", "flex", "short", "0.375", "0.0375", "2.25")
        add("gpt-5.4-nano", "flex", "short", "0.10", "0.01", "0.625")
        add("gpt-5.4-pro", "flex", "short", "15.00", None, "90.00")
        add("gpt-5.4-pro", "flex", "long", "30.00", None, "135.00")

        # Priority tier.
        add("gpt-5.5", "priority", "short", "12.50", "1.25", "75.00")
        add("gpt-5.4", "priority", "short", "5.00", "0.50", "30.00")
        add("gpt-5.4-mini", "priority", "short", "1.50", "0.15", "9.00")

        # Specialized models.
        add("chat-latest", "standard", "short", "5.00", "0.50", "30.00")
        add("gpt-5.3-codex", "standard", "short", "1.75", "0.175", "14.00")
        add("gpt-5.3-codex", "priority", "short", "3.50", "0.35", "28.00")
        return {(rate.model, rate.service_tier, rate.context): rate for rate in rows}

    def get_rate(self, model: str, service_tier: str = "standard", context: str = "short") -> ModelRate | None:
        return self._rates.get((model, service_tier, context))

    def calculate(
        self,
        *,
        model: str,
        usage: TokenUsage,
        service_tier: str = "standard",
        context: str = "short",
        regional_uplift: bool = False,
        tool_charges_usd: Decimal = Decimal("0"),
    ) -> dict[str, Any]:
        if model == "deterministic-local-no-llm":
            return {
                "status": "complete",
                "pricing_version": PRICING_VERSION,
                "pricing_source": "local_no_llm",
                "model": model,
                "service_tier": service_tier,
                "context": context,
                "rates": None,
                "usage": usage.to_dict(),
                "cost_breakdown_usd": {
                    "input": "0.000000",
                    "cached_input": "0.000000",
                    "output": "0.000000",
                    "tool_calls": "0.000000",
                    "regional_uplift": "0.000000",
                    "total": "0.000000",
                },
            }
        rate = self.get_rate(model, service_tier, context)
        if rate is None or rate.input_per_1m is None or rate.output_per_1m is None:
            return {
                "status": "not_answerable",
                "pricing_version": PRICING_VERSION,
                "pricing_source": PRICING_SOURCE_URL,
                "model": model,
                "service_tier": service_tier,
                "context": context,
                "rates": None if rate is None else rate.to_dict(),
                "usage": usage.to_dict(),
                "reason": "missing_official_rate_for_model_or_tier",
            }
        cached_rate = rate.cached_input_per_1m if rate.cached_input_per_1m is not None else rate.input_per_1m
        input_cost = Decimal(usage.billable_input_tokens) / USD_PER_MILLION * rate.input_per_1m
        cached_cost = Decimal(usage.cached_input_tokens) / USD_PER_MILLION * cached_rate
        output_cost = Decimal(usage.output_tokens) / USD_PER_MILLION * rate.output_per_1m
        subtotal = input_cost + cached_cost + output_cost + tool_charges_usd
        uplift = subtotal * Decimal("0.10") if regional_uplift else Decimal("0")
        total = subtotal + uplift
        return {
            "status": "complete",
            "pricing_version": PRICING_VERSION,
            "pricing_source": PRICING_SOURCE_URL,
            "reasoning_source": REASONING_SOURCE_URL,
            "model": model,
            "service_tier": service_tier,
            "context": context,
            "regional_uplift": regional_uplift,
            "rates": rate.to_dict(),
            "usage": usage.to_dict(),
            "cost_breakdown_usd": {
                "input": money(input_cost),
                "cached_input": money(cached_cost),
                "output": money(output_cost),
                "tool_calls": money(tool_charges_usd),
                "regional_uplift": money(uplift),
                "total": money(total),
            },
        }

    def as_json(self) -> dict[str, Any]:
        return {
            "pricing_version": PRICING_VERSION,
            "pricing_source": PRICING_SOURCE_URL,
            "reasoning_source": REASONING_SOURCE_URL,
            "rates": [rate.to_dict() for rate in sorted(self._rates.values(), key=lambda item: (item.model, item.service_tier, item.context))],
        }


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def parse_money(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value))


def normalize_usage(raw_usage: dict[str, Any] | None, *, fallback_input_tokens: int = 0, fallback_output_tokens: int = 0) -> TokenUsage:
    if not raw_usage:
        return TokenUsage(
            input_tokens=fallback_input_tokens,
            cached_input_tokens=0,
            output_tokens=fallback_output_tokens,
            reasoning_tokens=0,
            total_tokens=fallback_input_tokens + fallback_output_tokens,
            usage_source="local_estimate",
        )
    input_tokens = int(raw_usage.get("input_tokens", raw_usage.get("prompt_tokens", 0)) or 0)
    output_tokens = int(raw_usage.get("output_tokens", raw_usage.get("completion_tokens", 0)) or 0)
    input_details = raw_usage.get("input_tokens_details") or raw_usage.get("prompt_tokens_details") or {}
    output_details = raw_usage.get("output_tokens_details") or raw_usage.get("completion_tokens_details") or {}
    cached = int(raw_usage.get("input_cached_tokens", input_details.get("cached_tokens", 0)) or 0)
    reasoning = int(output_details.get("reasoning_tokens", raw_usage.get("reasoning_tokens", 0)) or 0)
    total = int(raw_usage.get("total_tokens", input_tokens + output_tokens) or 0)
    return TokenUsage(
        input_tokens=input_tokens,
        cached_input_tokens=cached,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning,
        total_tokens=total,
        usage_source=raw_usage.get("usage_source", "api_usage"),
    )
