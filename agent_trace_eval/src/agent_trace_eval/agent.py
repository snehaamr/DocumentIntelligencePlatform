"""FastPay exception copilot: a small traced ReAct loop (~200 lines)."""

from __future__ import annotations

import json
import time
from typing import Any

from opentelemetry.trace import Status, StatusCode, Tracer

from agent_trace_eval.guardrail import Guardrail
from agent_trace_eval.ledger import Ledger
from agent_trace_eval.llm import LLM, default_llm
from agent_trace_eval.models import AgentResult, ToolCall
from agent_trace_eval.telemetry import (
    chat_span,
    execute_tool_span,
    guardrail_span,
    invoke_agent_span,
    retrieval_span,
    set_json,
)
from agent_trace_eval.tools import TOOL_DEFS, Toolbox

SYSTEM = """You are FastPay Exception Copilot, an ops agent for payment exceptions.
Always lookup the payment (and exception) before mutating. Search runbooks for the reason_code.
Never refund more than the captured amount. Never retry succeeded, processing, or fraud payments.
Never echo PII (email, PAN, SSN). Final answer MUST be JSON:
{"action":"retry|refund|escalate|acknowledge|no_action","payment_id":"...|null","amount_cents":null,"reason":"...","evidence":["status=..."]}
Every evidence item must appear in tool output."""

DESC = {t["name"]: t["description"] for t in TOOL_DEFS}


class ExceptionCopilot:
    name = "fastpay-exception-copilot"

    def __init__(self, llm: LLM | None = None, ledger: Ledger | None = None, tracer: Tracer | None = None, max_turns: int = 8) -> None:
        self.llm = llm or default_llm()
        self.tools = Toolbox((ledger or Ledger()).clone())
        self.guard = Guardrail()
        self.tracer = tracer
        self.max_turns = max_turns

    def run(self, prompt: str, *, conversation_id: str | None = None) -> AgentResult:
        started = time.perf_counter()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ]
        calls: list[ToolCall] = []
        results: list[dict[str, Any]] = []
        schema_errors: list[str] = []
        blocks: list[str] = []
        in_tok = out_tok = 0
        final_text = ""
        tracer = self.tracer
        if tracer is None:
            return self._loop(prompt, conversation_id, messages, calls, results, schema_errors, blocks, in_tok, out_tok, started)
        with invoke_agent_span(tracer, agent_name=self.name, conversation_id=conversation_id, model=self.llm.model, prompt=prompt) as span:
            result = self._loop(prompt, conversation_id, messages, calls, results, schema_errors, blocks, in_tok, out_tok, started, span)
            span.set_attribute("gen_ai.usage.input_tokens", result.input_tokens)
            span.set_attribute("gen_ai.usage.output_tokens", result.output_tokens)
            set_json(span, "gen_ai.output.messages", [{"role": "assistant", "parts": [{"type": "text", "content": result.final_text}]}])
            if result.schema_errors:
                span.set_status(Status(StatusCode.ERROR, "schema_invalid"))
            return result

    def _loop(self, prompt, conversation_id, messages, calls, results, schema_errors, blocks, in_tok, out_tok, started, span=None) -> AgentResult:
        final_text = ""
        for turn in range(1, self.max_turns + 1):
            if self.tracer:
                with chat_span(self.tracer, model=self.llm.model, provider=self.llm.provider) as cspan:
                    reply = self.llm.complete(messages, TOOL_DEFS)
                    cspan.set_attribute("gen_ai.usage.input_tokens", reply.input_tokens)
                    cspan.set_attribute("gen_ai.usage.output_tokens", reply.output_tokens)
                    cspan.set_attribute("gen_ai.response.finish_reasons", (reply.finish_reason,))
            else:
                reply = self.llm.complete(messages, TOOL_DEFS)
            in_tok += reply.input_tokens
            out_tok += reply.output_tokens
            if not reply.tool_calls:
                final_text = reply.text or ""
                break
            messages.append({"role": "assistant", "tool_calls": [tc.model_dump() for tc in reply.tool_calls]})
            for tc in reply.tool_calls:
                calls.append(tc)
                payload = self._exec(tc, schema_errors, blocks)
                results.append({"name": tc.name, "arguments": tc.arguments, "result": payload})
                messages.append({"role": "tool", "name": tc.name, "tool_call_id": tc.id, "content": json.dumps(payload)})
        else:
            final_text = json.dumps({"action": "no_action", "reason": "max turns", "evidence": []})
        parsed = _parse(final_text)
        return AgentResult(
            final_text=final_text,
            action=parsed.get("action"),
            payment_id=parsed.get("payment_id"),
            amount_cents=parsed.get("amount_cents"),
            tool_calls=calls,
            tool_results=results,
            schema_errors=schema_errors,
            guardrail_blocks=blocks,
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=(time.perf_counter() - started) * 1000,
            model=self.llm.model,
            turns=min(turn, self.max_turns),
        )

    def _exec(self, tc: ToolCall, schema_errors: list[str], blocks: list[str]) -> dict[str, Any]:
        errors = self.tools.validate(tc.name, tc.arguments)
        if errors:
            schema_errors.extend(errors)
            return {"error": "schema_invalid", "details": errors}
        pay = self.tools.payment_snapshot(tc.arguments.get("payment_id"))
        decision = self.guard.check(tc.name, tc.arguments, pay)
        if self.tracer and tc.name in {"retry_payment", "refund_payment"}:
            with guardrail_span(self.tracer, policy_id=decision.policy_id, tool_name=tc.name) as gspan:
                gspan.set_attribute("gen_ai.guardrail.allowed", decision.allow)
                gspan.set_attribute("gen_ai.guardrail.reason", decision.reason)
                if not decision.allow:
                    gspan.set_status(Status(StatusCode.ERROR, decision.reason))
                    gspan.set_attribute("error.type", decision.policy_id)
        if not decision.allow:
            blocks.append(decision.reason)
            return {"error": decision.reason, "guardrail": decision.policy_id, "ok": False}
        if self.tracer:
            with execute_tool_span(self.tracer, tool_name=tc.name, call_id=tc.id, arguments=tc.arguments, description=DESC.get(tc.name, "")) as tspan:
                if tc.name == "search_runbook":
                    with retrieval_span(self.tracer, query=str(tc.arguments.get("query") or ""), top_k=int(tc.arguments.get("top_k") or 3)) as rspan:
                        result = self.tools.execute(tc.name, tc.arguments)
                        set_json(rspan, "gen_ai.retrieval.documents", result.get("documents") or [])
                else:
                    result = self.tools.execute(tc.name, tc.arguments)
                set_json(tspan, "gen_ai.tool.call.result", result)
                return result
        return self.tools.execute(tc.name, tc.arguments)


def _parse(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}
