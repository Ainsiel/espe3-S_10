"""PolicyEngine deny-by-default."""

from __future__ import annotations

from typing import Any

from .constants import PROHIBITED_TOOLS, SENSITIVE_APPROVALS
from .schemas import AgentSpec, ToolSpec


class PolicyDecision(Exception):
    def __init__(self, status: str, reason: str, required_approval: str | None = None) -> None:
        self.status = status
        self.reason = reason
        self.required_approval = required_approval
        super().__init__(reason)


class PolicyEngine:
    def assert_agent_allowed(self, agent: AgentSpec, state: dict[str, Any]) -> None:
        if agent.status != "approved":
            raise PolicyDecision("error", f"agent_not_approved:{agent.agent_id}")
        if state.get("approval", {}).get("status") == "rejected":
            raise PolicyDecision("needs_user_input", "approval_rejected")

    def evaluate_tool(self, agent: AgentSpec, tool: ToolSpec, state: dict[str, Any]) -> dict[str, Any]:
        if tool.tool_id in PROHIBITED_TOOLS:
            raise PolicyDecision("error", "policy_denied:prohibited_tool")
        if tool.tool_id not in agent.allowed_tools:
            raise PolicyDecision("error", "policy_denied:tool_not_allowlisted")
        missing = [permission for permission in tool.permissions if not agent.permissions.get(permission, False)]
        if missing:
            raise PolicyDecision("error", "policy_denied:missing_permission:" + ",".join(missing))
        approval = state.get("approval", {})
        if tool.approval_required and approval.get("status") != "approved":
            raise PolicyDecision("needs_user_input", "human_approval_required", "write")
        return {
            "status": "allow",
            "tool_id": tool.tool_id,
            "agent_id": agent.agent_id,
            "approval_status": approval.get("status", "none"),
        }

    def evaluate_requested_action(self, action: str, approval_status: str = "none") -> dict[str, Any]:
        if action in SENSITIVE_APPROVALS and approval_status != "approved":
            return {
                "status": "needs_user_input",
                "reason": "human_approval_required",
                "requested_action": action,
            }
        return {"status": "complete", "reason": "allowed"}


