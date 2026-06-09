"""BudgetManager para tokens, tool calls, latencia y ledger."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .hashing import hash_obj
from .pricing import PricingCatalog, normalize_usage, parse_money
from .schemas import AgentSpec
from .storage import FactoryStorage


class BudgetExceeded(Exception):
    pass


class BudgetManager:
    def __init__(self, storage: FactoryStorage) -> None:
        self.storage = storage
        self.pricing = PricingCatalog()
        self._ledger = {
            "run_id": "RUN-TBD",
            "currency": "USD",
            "pricing_version": self.pricing.as_json()["pricing_version"],
            "pricing_source": self.pricing.as_json()["pricing_source"],
            "phases": [],
            "totals": {
                "input_tokens": 0,
                "billable_input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "reasoning_tokens": 0,
                "tool_calls": 0,
                "latency_ms": 0,
                "estimated_cost": "0.000000",
                "model_requests": 0,
            },
        }

    def estimate_tokens(self, value: Any) -> int:
        text = str(value)
        return max(1, len(text) // 4) if text else 0

    def assert_available(self, agent: AgentSpec, state: dict[str, Any]) -> None:
        budget = state.get("budget", {})
        if budget.get("used_tool_calls", 0) > agent.budget.max_tool_calls:
            raise BudgetExceeded("budget_exceeded:tool_calls")
        if budget.get("used_input_tokens", 0) > agent.budget.max_input_tokens:
            raise BudgetExceeded("budget_exceeded:input_tokens")

    def record_agent(
        self,
        *,
        run_id: str,
        phase: str,
        agent: AgentSpec,
        input_payload: Any,
        output_payload: Any,
        tool_calls: int,
        latency_ms: int = 0,
        api_usage: dict[str, Any] | None = None,
        model_override: str | None = None,
        service_tier: str = "standard",
        context: str = "short",
        regional_uplift: bool = False,
        tool_charges_usd: str | Decimal = "0",
    ) -> dict[str, Any]:
        fallback_input_tokens = self.estimate_tokens(input_payload)
        fallback_output_tokens = self.estimate_tokens(output_payload)
        usage = normalize_usage(
            api_usage,
            fallback_input_tokens=fallback_input_tokens,
            fallback_output_tokens=fallback_output_tokens,
        )
        model = model_override or agent.model_policy.get("model", "deterministic-local-no-llm")
        pricing = self.pricing.calculate(
            model=model,
            usage=usage,
            service_tier=service_tier,
            context=context,
            regional_uplift=regional_uplift,
            tool_charges_usd=parse_money(tool_charges_usd),
        )
        total_cost = pricing.get("cost_breakdown_usd", {}).get("total", "0.000000")
        entry = {
            "phase": phase,
            "agent_id": agent.agent_id,
            "model": model,
            "service_tier": service_tier,
            "context": context,
            "usage_source": usage.usage_source,
            "billing_is_real_api_usage": usage.usage_source == "api_usage",
            "input_tokens": usage.input_tokens,
            "billable_input_tokens": usage.billable_input_tokens,
            "output_tokens": usage.output_tokens,
            "cached_tokens": usage.cached_input_tokens,
            "reasoning_tokens": usage.reasoning_tokens,
            "visible_output_tokens": usage.visible_output_tokens,
            "tool_calls": tool_calls,
            "latency_ms": latency_ms,
            "estimated_cost": total_cost,
            "cost_status": pricing["status"],
            "cost_breakdown_usd": pricing.get("cost_breakdown_usd"),
            "pricing": {
                "pricing_version": pricing["pricing_version"],
                "pricing_source": pricing["pricing_source"],
                "reasoning_source": pricing.get("reasoning_source"),
                "rates": pricing.get("rates"),
                "reason": pricing.get("reason"),
            },
            "input_hash": hash_obj(input_payload),
            "output_hash": hash_obj(output_payload),
        }
        self._ledger["run_id"] = run_id
        self._ledger["phases"].append(entry)
        totals = self._ledger["totals"]
        totals["input_tokens"] += usage.input_tokens
        totals["billable_input_tokens"] += usage.billable_input_tokens
        totals["output_tokens"] += usage.output_tokens
        totals["cached_tokens"] += usage.cached_input_tokens
        totals["reasoning_tokens"] += usage.reasoning_tokens
        totals["tool_calls"] += tool_calls
        totals["latency_ms"] += latency_ms
        totals["model_requests"] += 1
        totals["estimated_cost"] = str((parse_money(totals["estimated_cost"]) + parse_money(total_cost)).quantize(Decimal("0.000001")))
        self.storage.write_json("billing-ledger.json", self._ledger)
        self.storage.write_json(self.storage.run_dir / "billing-ledger.json", self._ledger)
        self._sync_derived_reports()
        return entry

    def ledger(self) -> dict[str, Any]:
        return dict(self._ledger)

    def _sync_derived_reports(self) -> None:
        real_api_requests = sum(1 for phase in self._ledger["phases"] if phase.get("billing_is_real_api_usage"))
        totals = self._ledger["totals"]
        cost_report = self.storage.read_json("cost-report.json", default=None)
        if isinstance(cost_report, dict):
            cost_report["model_calls"] = totals["model_requests"]
            cost_report["real_api_model_calls"] = real_api_requests
            cost_report["local_estimate_model_calls"] = max(0, totals["model_requests"] - real_api_requests)
            cost_report["external_cost_usd"] = totals["estimated_cost"]
            cost_report["billing_hash"] = hash_obj(self._ledger)
            self.storage.write_json("cost-report.json", cost_report)
        final_report = self.storage.read_json("final-report.json", default=None)
        if isinstance(final_report, dict):
            final_report["costs"] = self._ledger
            self.storage.write_json("final-report.json", final_report)
