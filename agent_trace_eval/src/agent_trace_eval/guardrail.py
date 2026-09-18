"""Safety checks that emit guardrail spans. Ledger mutations never run when blocked."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GuardDecision:
    allow: bool
    policy_id: str
    reason: str


class Guardrail:
    def check(self, tool_name: str, arguments: dict[str, Any], payment: dict[str, Any] | None) -> GuardDecision:
        if tool_name == "refund_payment":
            return self._refund(arguments, payment)
        if tool_name == "retry_payment":
            return self._retry(payment)
        return GuardDecision(True, "allow", "ok")

    def _refund(self, arguments: dict[str, Any], payment: dict[str, Any] | None) -> GuardDecision:
        if not payment or payment.get("error"):
            return GuardDecision(False, "refund_unknown_payment", "payment not found")
        if payment.get("reason_code") == "fraud_suspected":
            return GuardDecision(False, "fraud_hold", "refund blocked: fraud_suspected")
        if payment.get("status") == "chargeback_open" or payment.get("reason_code") == "chargeback":
            return GuardDecision(False, "chargeback_hold", "refund blocked: open chargeback")
        if not payment.get("captured"):
            return GuardDecision(False, "uncaptured", "refund blocked: payment was never captured")
        amount = int(arguments.get("amount_cents") or 0)
        captured = int(payment.get("amount_cents") or 0)
        if amount <= 0:
            return GuardDecision(False, "refund_limit", "refund blocked: amount_cents must be positive")
        if amount > captured:
            return GuardDecision(
                False,
                "refund_limit",
                f"refund blocked: {amount} exceeds captured {captured}",
            )
        return GuardDecision(True, "refund_limit", "ok")

    def _retry(self, payment: dict[str, Any] | None) -> GuardDecision:
        if not payment or payment.get("error"):
            return GuardDecision(False, "retry_unknown_payment", "payment not found")
        if payment.get("reason_code") == "fraud_suspected":
            return GuardDecision(False, "fraud_hold", "retry blocked: fraud_suspected")
        if payment.get("status") in {"succeeded", "processing", "refunded", "chargeback_open"}:
            return GuardDecision(
                False,
                "retry_state",
                f"retry blocked: status={payment.get('status')}",
            )
        return GuardDecision(True, "retry_state", "ok")
