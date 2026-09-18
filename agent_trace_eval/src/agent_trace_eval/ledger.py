"""Deterministic FastPay ledger. Cloned per agent run so CI stays isolated."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"


def _load_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text())


class Ledger:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        data = payload if payload is not None else _load_json("ledger.json")
        self.payments = {p["payment_id"]: p for p in data["payments"]}
        self.exceptions = {e["exception_id"]: e for e in data["exceptions"]}
        self.customers = {c["customer_id"]: c for c in data["customers"]}

    def clone(self) -> "Ledger":
        return Ledger(
            {
                "payments": [deepcopy(p) for p in self.payments.values()],
                "exceptions": [deepcopy(e) for e in self.exceptions.values()],
                "customers": [deepcopy(c) for c in self.customers.values()],
            }
        )

    def lookup_payment(self, payment_id: str) -> dict[str, Any]:
        pay = self.payments.get(payment_id)
        if not pay:
            return {"error": "not_found", "payment_id": payment_id}
        view = dict(pay)
        retries = int(pay.get("retry_count") or 0)
        if pay.get("reason_code") in {"network_timeout", "3ds_timeout"}:
            view["retry_exhausted"] = retries >= 1
        else:
            view["retry_exhausted"] = retries >= 2
        return view

    def list_exceptions(
        self,
        exception_id: str | None = None,
        payment_id: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        items = list(self.exceptions.values())
        if exception_id:
            items = [e for e in items if e["exception_id"] == exception_id]
        if payment_id:
            items = [e for e in items if e["payment_id"] == payment_id]
        if status:
            items = [e for e in items if e["status"] == status]
        return {"items": items, "count": len(items)}

    def get_customer(self, customer_id: str) -> dict[str, Any]:
        cust = self.customers.get(customer_id)
        if not cust:
            return {"error": "not_found", "customer_id": customer_id}
        return dict(cust)

    def retry_payment(self, payment_id: str) -> dict[str, Any]:
        pay = self.payments.get(payment_id)
        if not pay:
            return {"error": "not_found", "payment_id": payment_id}
        pay["retry_count"] = int(pay.get("retry_count") or 0) + 1
        pay["status"] = "processing"
        return {"ok": True, "payment_id": payment_id, "status": pay["status"], "action": "retry"}

    def refund_payment(self, payment_id: str, amount_cents: int) -> dict[str, Any]:
        pay = self.payments.get(payment_id)
        if not pay:
            return {"error": "not_found", "payment_id": payment_id}
        pay["status"] = "refunded"
        return {
            "ok": True,
            "payment_id": payment_id,
            "amount_cents": amount_cents,
            "status": "refunded",
            "action": "refund",
        }

    def escalate_to_ops(self, payment_id: str, severity: str, reason: str) -> dict[str, Any]:
        return {
            "ok": True,
            "payment_id": payment_id,
            "severity": severity,
            "reason": reason,
            "action": "escalate",
            "ticket_queue": "risk" if severity == "high" else "ops",
        }

    def acknowledge_exception(self, exception_id: str) -> dict[str, Any]:
        exc = self.exceptions.get(exception_id)
        if not exc:
            return {"error": "not_found", "exception_id": exception_id}
        exc["status"] = "acked"
        return {
            "ok": True,
            "exception_id": exception_id,
            "payment_id": exc["payment_id"],
            "status": "acked",
            "action": "acknowledge",
        }
