"""LLM protocol: heuristic policy model for CI, optional OpenAI adapter."""

from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any, Protocol

from agent_trace_eval.models import LLMResponse, ToolCall
from agent_trace_eval.pricing import estimate_tokens
from agent_trace_eval.retrieval import RunbookIndex

PAY_RE = re.compile(r"PAY-\d+")
EXC_RE = re.compile(r"EXC-\d+")
MONEY_RE = re.compile(r"\$([0-9]+(?:\.[0-9]{1,2})?)")


class LLM(Protocol):
    model: str
    provider: str

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse: ...


def _call(name: str, arguments: dict[str, Any]) -> LLMResponse:
    payload = json.dumps({"tool": name, "arguments": arguments})
    return LLMResponse(
        tool_calls=[ToolCall(id=f"call_{uuid.uuid4().hex[:12]}", name=name, arguments=arguments)],
        input_tokens=24,
        output_tokens=estimate_tokens(payload),
        model="heuristic",
        provider="heuristic",
        finish_reason="tool_calls",
    )


def _final(payload: dict[str, Any], input_tokens: int) -> LLMResponse:
    text = json.dumps(payload)
    return LLMResponse(
        text=text,
        input_tokens=input_tokens,
        output_tokens=estimate_tokens(text),
        model="heuristic",
        provider="heuristic",
        finish_reason="stop",
    )


def _intent(text: str) -> str:
    low = text.lower()
    if any(w in low for w in ("refund", "reverse", "chargeback goodwill")):
        return "refund"
    if "retry" in low or "push it through" in low:
        return "retry"
    if "escalate" in low or "risk queue" in low:
        return "escalate"
    if "acknowledge" in low or "close it out" in low or "close it" in low:
        return "acknowledge"
    return "policy"


def _results(messages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for msg in messages:
        if msg.get("role") != "tool":
            continue
        try:
            body = json.loads(msg.get("content") or "{}")
        except json.JSONDecodeError:
            body = {"raw": msg.get("content")}
        grouped.setdefault(str(msg.get("name")), []).append(body)
    return grouped


def _looked_up_ids(grouped: dict[str, list[dict[str, Any]]]) -> set[str]:
    ids: set[str] = set()
    for item in grouped.get("lookup_payment", []):
        if item.get("payment_id") and not item.get("error"):
            ids.add(item["payment_id"])
    return ids


class HeuristicLLM:
    """Deterministic runbook follower. Exercises the same tool loop as a hosted model."""

    model = "heuristic"
    provider = "heuristic"

    def __init__(self) -> None:
        self.index = RunbookIndex()

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse:
        user = next(m["content"] for m in messages if m.get("role") == "user")
        grouped = _results(messages)
        called = set(grouped)
        prompt_tokens = estimate_tokens(json.dumps(messages))
        pay_ids = PAY_RE.findall(user)
        exc_ids = EXC_RE.findall(user)

        if not pay_ids and not exc_ids:
            if "escalate_to_ops" not in called:
                return _call(
                    "escalate_to_ops",
                    {
                        "payment_id": "UNKNOWN",
                        "severity": "medium",
                        "reason": "ticket has no payment or exception id",
                    },
                )
            return _final(
                {
                    "action": "escalate",
                    "payment_id": None,
                    "amount_cents": None,
                    "reason": "no payment id on ticket",
                    "evidence": ["ticket has no payment or exception id"],
                },
                prompt_tokens,
            )

        if exc_ids and "list_exceptions" not in called:
            return _call("list_exceptions", {"exception_id": exc_ids[0]})

        if "list_exceptions" in grouped:
            for block in grouped["list_exceptions"]:
                for item in block.get("items") or []:
                    pid = item.get("payment_id")
                    if pid and pid not in pay_ids:
                        pay_ids.append(pid)

        looked = _looked_up_ids(grouped)
        for pid in pay_ids:
            if pid not in looked:
                return _call("lookup_payment", {"payment_id": pid})

        payments = [p for p in grouped.get("lookup_payment", []) if not p.get("error")]
        target = next((p for p in payments if p.get("status") == "failed"), None)
        if target is None:
            target = next((p for p in payments if p.get("status") not in {"succeeded", "refunded"}), None)
        if target is None and payments:
            target = payments[0]

        if target and "search_runbook" not in called:
            query = target.get("reason_code") or target.get("status") or "unknown"
            return _call("search_runbook", {"query": str(query), "top_k": 3})

        runbook = (grouped.get("search_runbook") or [{}])[-1]
        policy = self.index.match_action(target or {}, runbook) if target else "escalate"
        intent = _intent(user)
        money = MONEY_RE.search(user)
        requested = int(round(float(money.group(1)) * 100)) if money else None

        if target is None:
            return _final(
                {"action": "escalate", "payment_id": None, "reason": "payment not in ledger", "evidence": []},
                prompt_tokens,
            )

        pid = target["payment_id"]
        last_err = None
        for name, blocks in grouped.items():
            for block in blocks:
                if isinstance(block, dict) and block.get("error"):
                    last_err = block

        def evidence() -> list[str]:
            rows = [
                f"status={target.get('status')}",
                f"reason_code={target.get('reason_code')}",
                f"captured={target.get('captured')}",
                f"balance_recovered={target.get('balance_recovered')}",
                f"retry_exhausted={target.get('retry_exhausted')}",
                f"amount_cents={target.get('amount_cents')}",
            ]
            if last_err and last_err.get("error"):
                rows.append(str(last_err["error"]))
            return [r for r in rows if "None" not in r]

        # Honor safety/policy over the user's requested mutation.
        if policy == "escalate" and intent in {"retry", "refund", "policy", "acknowledge"}:
            if "escalate_to_ops" not in called:
                severity = "high" if target.get("reason_code") == "fraud_suspected" else "medium"
                return _call(
                    "escalate_to_ops",
                    {"payment_id": pid, "severity": severity, "reason": f"runbook requires escalate for {target.get('reason_code')}"},
                )
            return _final(
                {
                    "action": "escalate",
                    "payment_id": pid,
                    "amount_cents": None,
                    "reason": f"runbook escalate for {target.get('reason_code')}",
                    "evidence": evidence(),
                },
                prompt_tokens,
            )

        if intent == "refund":
            amount = requested if requested is not None else int(target.get("amount_cents") or 0)
            if "refund_payment" not in called:
                return _call("refund_payment", {"payment_id": pid, "amount_cents": amount})
            refund = grouped["refund_payment"][-1]
            if refund.get("ok"):
                return _final(
                    {
                        "action": "refund",
                        "payment_id": pid,
                        "amount_cents": amount,
                        "reason": "captured payment refunded",
                        "evidence": evidence() + [f"amount_cents={amount}"],
                    },
                    prompt_tokens,
                )
            return _final(
                {
                    "action": "no_action",
                    "payment_id": pid,
                    "amount_cents": amount,
                    "reason": str(refund.get("error") or "refund blocked"),
                    "evidence": evidence(),
                },
                prompt_tokens,
            )

        if intent == "retry":
            if policy == "acknowledge":
                return self._finish_policy(policy, pid, target, grouped, called, evidence, prompt_tokens)
            if "retry_payment" not in called:
                return _call("retry_payment", {"payment_id": pid})
            retry = grouped["retry_payment"][-1]
            if retry.get("ok"):
                return _final(
                    {"action": "retry", "payment_id": pid, "reason": "retry submitted", "evidence": evidence()},
                    prompt_tokens,
                )
            action = "escalate" if target.get("reason_code") == "fraud_suspected" else "no_action"
            if action == "escalate" and "escalate_to_ops" not in called:
                return _call(
                    "escalate_to_ops",
                    {"payment_id": pid, "severity": "high", "reason": "fraud hold"},
                )
            return _final(
                {"action": action, "payment_id": pid, "reason": str(retry.get("error") or "retry blocked"), "evidence": evidence()},
                prompt_tokens,
            )

        return self._finish_policy(policy or "no_action", pid, target, grouped, called, evidence, prompt_tokens)

    def _finish_policy(
        self,
        policy: str,
        pid: str,
        target: dict[str, Any],
        grouped: dict[str, list[dict[str, Any]]],
        called: set[str],
        evidence,
        prompt_tokens: int,
    ) -> LLMResponse:
        if policy == "retry" and "retry_payment" not in called:
            return _call("retry_payment", {"payment_id": pid})
        if policy == "acknowledge" and "acknowledge_exception" not in called:
            exc = target.get("open_exception_id")
            if exc:
                return _call("acknowledge_exception", {"exception_id": exc})
        if policy == "escalate" and "escalate_to_ops" not in called:
            return _call(
                "escalate_to_ops",
                {
                    "payment_id": pid,
                    "severity": "high" if target.get("reason_code") == "fraud_suspected" else "medium",
                    "reason": f"runbook {policy}",
                },
            )
        if policy == "retry" and grouped.get("retry_payment") and not grouped["retry_payment"][-1].get("ok"):
            policy = "no_action"
        return _final(
            {
                "action": policy,
                "payment_id": pid,
                "amount_cents": None,
                "reason": f"runbook action {policy}",
                "evidence": evidence(),
            },
            prompt_tokens,
        )


class OpenAILLM:
    model: str
    provider = "openai"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        from openai import OpenAI

        self.model = model
        self.client = OpenAI()

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse:
        oai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in tools
        ]
        mapped = []
        for msg in messages:
            if msg.get("role") == "tool":
                mapped.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.get("tool_call_id"),
                        "content": msg.get("content") or "",
                    }
                )
            elif msg.get("tool_calls"):
                mapped.append(
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["arguments"]),
                                },
                            }
                            for tc in msg["tool_calls"]
                        ],
                    }
                )
            else:
                mapped.append({"role": msg["role"], "content": msg.get("content") or ""})
        resp = self.client.chat.completions.create(
            model=self.model, messages=mapped, tools=oai_tools, temperature=0
        )
        choice = resp.choices[0]
        usage = resp.usage
        calls: list[ToolCall] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments or "{}"),
                    )
                )
        return LLMResponse(
            text=choice.message.content,
            tool_calls=calls,
            input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            model=self.model,
            provider="openai",
            finish_reason=choice.finish_reason or "stop",
        )


def default_llm() -> LLM:
    if os.getenv("OPENAI_API_KEY"):
        return OpenAILLM(os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    return HeuristicLLM()
