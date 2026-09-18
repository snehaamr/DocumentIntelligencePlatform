"""JSON-schema tool registry on top of the fake FastPay ledger."""

from __future__ import annotations

from typing import Any, Callable

from jsonschema import Draft202012Validator

from agent_trace_eval.ledger import Ledger
from agent_trace_eval.retrieval import RunbookIndex

TOOL_DEFS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "lookup_payment",
        "description": "Fetch a payment from the FastPay ledger by payment_id.",
        "parameters": {
            "type": "object",
            "properties": {"payment_id": {"type": "string", "pattern": "^PAY-[0-9]+$"}},
            "required": ["payment_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_exceptions",
        "description": "List payment exceptions, optionally filtered.",
        "parameters": {
            "type": "object",
            "properties": {
                "exception_id": {"type": "string", "pattern": "^EXC-[0-9]+$"},
                "payment_id": {"type": "string", "pattern": "^PAY-[0-9]+$"},
                "status": {"type": "string", "enum": ["open", "acked"]},
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_customer",
        "description": "Fetch customer profile. Response contains PII; do not echo it in the final answer.",
        "parameters": {
            "type": "object",
            "properties": {"customer_id": {"type": "string", "pattern": "^CUS-[0-9]+$"}},
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_runbook",
        "description": "Retrieve ops runbooks for a failure reason or status.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 2},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 5},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "retry_payment",
        "description": "Re-submit a failed payment. Guardrail blocks succeeded/processing/fraud.",
        "parameters": {
            "type": "object",
            "properties": {"payment_id": {"type": "string", "pattern": "^PAY-[0-9]+$"}},
            "required": ["payment_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "refund_payment",
        "description": "Refund a captured payment. Amount must not exceed captured amount_cents.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "pattern": "^PAY-[0-9]+$"},
                "amount_cents": {"type": "integer", "minimum": 1},
            },
            "required": ["payment_id", "amount_cents"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "escalate_to_ops",
        "description": "Open an ops/risk ticket when the runbook requires a human.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                "reason": {"type": "string", "minLength": 3},
            },
            "required": ["payment_id", "severity", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "acknowledge_exception",
        "description": "Mark an exception as acknowledged after following the runbook.",
        "parameters": {
            "type": "object",
            "properties": {"exception_id": {"type": "string", "pattern": "^EXC-[0-9]+$"}},
            "required": ["exception_id"],
            "additionalProperties": False,
        },
    },
]


class Toolbox:
    def __init__(self, ledger: Ledger, index: RunbookIndex | None = None) -> None:
        self.ledger = ledger
        self.index = index or RunbookIndex()
        self._validators = {
            spec["name"]: Draft202012Validator(spec["parameters"]) for spec in TOOL_DEFS
        }
        self._handlers: dict[str, Callable[..., dict[str, Any]]] = {
            "lookup_payment": lambda **kw: self.ledger.lookup_payment(kw["payment_id"]),
            "list_exceptions": lambda **kw: self.ledger.list_exceptions(
                exception_id=kw.get("exception_id"),
                payment_id=kw.get("payment_id"),
                status=kw.get("status"),
            ),
            "get_customer": lambda **kw: self.ledger.get_customer(kw["customer_id"]),
            "search_runbook": lambda **kw: self.index.search(kw["query"], int(kw.get("top_k") or 3)),
            "retry_payment": lambda **kw: self.ledger.retry_payment(kw["payment_id"]),
            "refund_payment": lambda **kw: self.ledger.refund_payment(
                kw["payment_id"], int(kw["amount_cents"])
            ),
            "escalate_to_ops": lambda **kw: self.ledger.escalate_to_ops(
                kw["payment_id"], kw["severity"], kw["reason"]
            ),
            "acknowledge_exception": lambda **kw: self.ledger.acknowledge_exception(kw["exception_id"]),
        }

    def validate(self, name: str, arguments: dict[str, Any]) -> list[str]:
        if name not in self._validators:
            return [f"unknown tool: {name}"]
        return [e.message for e in self._validators[name].iter_errors(arguments)]

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._handlers[name](**arguments)

    def payment_snapshot(self, payment_id: str | None) -> dict[str, Any] | None:
        if not payment_id:
            return None
        return self.ledger.lookup_payment(payment_id)
