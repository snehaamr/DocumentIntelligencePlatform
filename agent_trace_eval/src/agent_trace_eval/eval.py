"""Deterministic eval metrics: tools, schema, groundedness, cost, PII — not LLM-as-judge."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from agent_trace_eval.models import AgentResult, EvalReport, TaskScore, TaskSpec
from agent_trace_eval.pricing import cost_usd
from agent_trace_eval.telemetry import EMAIL_RE

PAY_RE = re.compile(r"PAY-\d+")


def _called_names(result: AgentResult) -> list[str]:
    return [c.name for c in result.tool_calls]


def tool_recall(called: list[str], expected: list[str]) -> float:
    if not expected:
        return 1.0
    got = set(called)
    return sum(1 for name in expected if name in got) / len(expected)


def tool_precision(called: list[str], expected: list[str], optional: list[str], forbidden: list[str]) -> float:
    if not called:
        return 1.0
    allowed = set(expected) | set(optional)
    # Forbidden calls are never allowed, even if listed optional.
    allowed -= set(forbidden)
    return sum(1 for name in called if name in allowed) / len(called)


def groundedness(result: AgentResult, prompt: str) -> float:
    corpus = "\n".join(json.dumps(item) for item in result.tool_results).lower()
    try:
        data = json.loads(result.final_text)
    except json.JSONDecodeError:
        return 0.0
    if not isinstance(data, dict):
        return 0.0
    if not result.tool_results:
        invented = [p for p in PAY_RE.findall(result.final_text) if p not in prompt]
        return 0.0 if invented else 1.0
    checks: list[str] = [str(e) for e in data.get("evidence") or []]
    if data.get("payment_id"):
        checks.append(str(data["payment_id"]))
    if data.get("amount_cents") is not None:
        checks.append(str(data["amount_cents"]))
    if not checks:
        return 0.0
    hits = 0
    for item in checks:
        needle = item.lower()
        if needle in corpus or needle in prompt.lower():
            hits += 1
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            if key.lower() in corpus and value.lower() in corpus:
                hits += 1
    return hits / len(checks)


def pii_leaked(text: str) -> bool:
    return bool(EMAIL_RE.search(text or ""))


def score_task(spec: TaskSpec, result: AgentResult) -> TaskScore:
    called = _called_names(result)
    schema_valid = not result.schema_errors
    forbidden_hit = any(name in spec.forbidden_tools for name in called)
    payment_ok = spec.expected_payment_id is None or result.payment_id == spec.expected_payment_id
    success = (
        result.action == spec.expected_action
        and payment_ok
        and schema_valid
        and not forbidden_hit
    )
    detail = ""
    if not success:
        detail = (
            f"action={result.action!r} expected={spec.expected_action!r} "
            f"payment={result.payment_id!r} forbidden={forbidden_hit} schema={schema_valid}"
        )
    usd = cost_usd(result.model, result.input_tokens, result.output_tokens)
    return TaskScore(
        task_id=spec.id,
        success=success,
        action=result.action,
        expected_action=spec.expected_action,
        tool_precision=tool_precision(called, spec.expected_tools, spec.optional_tools, spec.forbidden_tools),
        tool_recall=tool_recall(called, spec.expected_tools),
        schema_valid=schema_valid,
        groundedness=groundedness(result, spec.prompt),
        pii_leaked=pii_leaked(result.final_text),
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=usd,
        turns=result.turns,
        detail=detail,
    )


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil(pct / 100 * len(ordered)) - 1))
    return ordered[idx]


def aggregate(scores: list[TaskScore]) -> EvalReport:
    n = len(scores) or 1
    return EvalReport(
        task_count=len(scores),
        success_rate=sum(s.success for s in scores) / n,
        schema_validity=sum(s.schema_valid for s in scores) / n,
        mean_tool_precision=sum(s.tool_precision for s in scores) / n,
        mean_tool_recall=sum(s.tool_recall for s in scores) / n,
        mean_groundedness=sum(s.groundedness for s in scores) / n,
        pii_leak_rate=sum(s.pii_leaked for s in scores) / n,
        usd_per_task=sum(s.cost_usd for s in scores) / n,
        p95_latency_ms=_percentile([s.latency_ms for s in scores], 95),
        total_cost_usd=sum(s.cost_usd for s in scores),
        scores=scores,
    )


def markdown_table(report: EvalReport) -> str:
    lines = [
        "| Task | Success | Action | Tools P/R | Grounded | Schema | Latency ms | USD |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in report.scores:
        mark = "pass" if s.success else "FAIL"
        lines.append(
            f"| `{s.task_id}` | {mark} | {s.action or '—'} → {s.expected_action} | "
            f"{s.tool_precision:.2f}/{s.tool_recall:.2f} | {s.groundedness:.2f} | "
            f"{'yes' if s.schema_valid else 'no'} | {s.latency_ms:.1f} | {s.cost_usd:.6f} |"
        )
    lines += [
        "",
        f"Success rate: **{report.success_rate:.0%}** · "
        f"Schema: **{report.schema_validity:.0%}** · "
        f"Groundedness: **{report.mean_groundedness:.2f}** · "
        f"$/task: **{report.usd_per_task:.6f}** · "
        f"p95 latency: **{report.p95_latency_ms:.1f} ms**",
    ]
    return "\n".join(lines)
