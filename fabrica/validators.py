"""ValidatorChain en orden fijo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import CLOSED_STATUSES, REQUIRED_OPERATIONAL_ARTIFACTS, SECRET_PATTERNS, VALIDATORS
from .schemas import AGENT_OUTPUT_KEYS
from .storage import FactoryStorage


class ValidationError(Exception):
    def __init__(self, validator_id: str, issue: str, next_action: str = "error") -> None:
        self.validator_id = validator_id
        self.issue = issue
        self.next_action = next_action
        super().__init__(issue)


class SchemaValidator:
    validator_id = "schema"

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        keys = set(output)
        if keys != AGENT_OUTPUT_KEYS:
            raise ValidationError(self.validator_id, "schema_unrecoverable:agent_output_keys")
        if output["status"] not in CLOSED_STATUSES:
            raise ValidationError(self.validator_id, "schema_unrecoverable:status")
        if output["next_action"] not in ("continue", "retry", "needs_user_input", "not_answerable", "error"):
            raise ValidationError(self.validator_id, "schema_unrecoverable:next_action")
        if not isinstance(output["artifacts"], list) or not isinstance(output["evidence"], list):
            raise ValidationError(self.validator_id, "schema_unrecoverable:list_fields")
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class EvidenceValidator:
    validator_id = "evidence"

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        if output["status"] == "complete" and not output["evidence"]:
            raise ValidationError(self.validator_id, "missing_critical_evidence", "not_answerable")
        for evidence in output["evidence"]:
            for field in ("evidence_id", "source_id", "chunk_id", "hash"):
                if field not in evidence:
                    raise ValidationError(self.validator_id, "missing_evidence_field:" + field, "not_answerable")
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": output["evidence"][0]["evidence_id"] if output["evidence"] else None}


class PolicyValidator:
    validator_id = "policy"

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        if any("policy_denied" in issue for issue in output["issues"]):
            raise ValidationError(self.validator_id, "policy_denied")
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class SafetyValidator:
    validator_id = "safety"

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        blob = str(output)
        for pattern in SECRET_PATTERNS:
            if pattern in blob:
                raise ValidationError(self.validator_id, "secret_detected")
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class ConsistencyValidator:
    validator_id = "consistency"

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        if output["agent_id"].startswith("agent.") is False:
            raise ValidationError(self.validator_id, "agent_id_invalid")
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class CoverageValidator:
    validator_id = "coverage"

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        if state.get("phase") in ("validate", "close") and output["status"] == "complete":
            if not output["artifacts"]:
                raise ValidationError(self.validator_id, "coverage_artifact_missing")
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class BudgetValidator:
    validator_id = "budget"

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        budget = state.get("budget", {})
        if budget.get("estimated_cost_usd", 0) > budget.get("max_cost_usd", 0):
            raise ValidationError(self.validator_id, "budget_exceeded")
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class ToolOutputValidator:
    validator_id = "tool-output"

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class FrontendQualityValidator:
    validator_id = "frontend_quality"

    DESIGN_ARTIFACTS = (
        "DESIGN_SYSTEM.md",
        "PRACTICAS_PERMANENTES.md",
        "design-tokens.json",
        "frontend-quality-contract.json",
    )
    UX_ARTIFACTS = (
        "ux-accessibility-report.json",
        "responsive-matrix.json",
    )
    VISUAL_ARTIFACTS = ("visual-qa-report.json",)

    def __init__(self, storage: FactoryStorage) -> None:
        self.storage = storage

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        phase = state.get("phase")
        required: tuple[str, ...] = ()
        if phase == "design_system":
            required = self.DESIGN_ARTIFACTS
        elif phase == "ux_accessibility":
            required = self.UX_ARTIFACTS
        elif phase == "frontend_validate":
            required = self.VISUAL_ARTIFACTS
        elif phase == "close":
            required = self.DESIGN_ARTIFACTS + self.UX_ARTIFACTS + self.VISUAL_ARTIFACTS
        missing = [name for name in required if not self.storage.path(name).exists()]
        if missing:
            raise ValidationError(self.validator_id, "frontend_quality_artifact_missing:" + ",".join(missing))
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class FinalFormatValidator:
    validator_id = "final_format"

    def __init__(self, storage: FactoryStorage) -> None:
        self.storage = storage

    def validate(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        if state.get("phase") != "close":
            return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}
        missing = [name for name in REQUIRED_OPERATIONAL_ARTIFACTS if not self.storage.path(name).exists()]
        if missing:
            raise ValidationError(self.validator_id, "missing_final_artifacts:" + ",".join(missing))
        return {"validator_id": self.validator_id, "status": "pass", "issues": [], "evidence_id": None}


class ValidatorChain:
    def __init__(self, storage: FactoryStorage) -> None:
        self.storage = storage
        self.validators = [
            SchemaValidator(),
            EvidenceValidator(),
            PolicyValidator(),
            SafetyValidator(),
            ConsistencyValidator(),
            CoverageValidator(),
            BudgetValidator(),
            ToolOutputValidator(),
            FrontendQualityValidator(storage),
            FinalFormatValidator(storage),
        ]

    def validate_all(self, output: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        reports: list[dict[str, Any]] = []
        try:
            for validator in self.validators:
                reports.append(validator.validate(output, state))
            status = "pass"
            blocking: list[str] = []
            retry_allowed = False
            next_action = output["next_action"]
        except ValidationError as error:
            reports.append(
                {
                    "validator_id": error.validator_id,
                    "status": "blocked",
                    "issues": [error.issue],
                    "evidence_id": None,
                }
            )
            status = "blocked"
            blocking = [error.issue]
            retry_allowed = error.next_action == "retry"
            next_action = error.next_action
        report = {
            "validation_id": "VAL-" + state["cycle_id"],
            "status": status,
            "validators": reports,
            "blocking_issues": blocking,
            "retry_allowed": retry_allowed,
            "next_action": next_action,
            "validator_order": list(VALIDATORS),
        }
        self.storage.write_json("validation-report.json", report)
        return report
