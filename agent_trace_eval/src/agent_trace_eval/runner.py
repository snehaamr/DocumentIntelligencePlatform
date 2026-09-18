"""Eval worker: pick up labeled tasks, run the copilot, score, emit traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from agent_trace_eval.agent import ExceptionCopilot
from agent_trace_eval.eval import aggregate, markdown_table, score_task
from agent_trace_eval.ledger import DATA_DIR, Ledger
from agent_trace_eval.llm import default_llm
from agent_trace_eval.models import EvalReport, TaskSpec
from agent_trace_eval.telemetry import configure_tracer, memory_exporter
from agent_trace_eval.tracehtml import spans_to_dicts, write_html, write_json


def load_tasks(path: Path | None = None) -> list[TaskSpec]:
    payload = json.loads((path or DATA_DIR / "tasks.json").read_text())
    return [TaskSpec.model_validate(item) for item in payload["tasks"]]


def load_thresholds(path: Path | None = None) -> dict[str, Any]:
    return yaml.safe_load((path or DATA_DIR / "thresholds.yaml").read_text())


def run_suite(
    tasks: list[TaskSpec] | None = None,
    *,
    out_dir: Path | None = None,
    export_traces: bool = True,
) -> EvalReport:
    tasks = tasks or load_tasks()
    tracer, memory = configure_tracer()
    scores = []
    for spec in tasks:
        agent = ExceptionCopilot(llm=default_llm(), ledger=Ledger(), tracer=tracer)
        result = agent.run(spec.prompt, conversation_id=f"task:{spec.id}")
        scores.append(score_task(spec, result))
    report = aggregate(scores)
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "latest.json").write_text(report.model_dump_json(indent=2))
        (out_dir / "latest.md").write_text(markdown_table(report) + "\n")
        if export_traces:
            spans = spans_to_dicts(list(memory.get_finished_spans()))
            write_json(out_dir / "spans.json", spans)
            write_html(out_dir / "trace.html", spans, title="FastPay exception copilot")
    return report


def gate_failures(report: EvalReport, thresholds: dict[str, Any] | None = None) -> list[str]:
    t = thresholds or load_thresholds()
    checks = [
        ("success_rate", report.success_rate, ">=", t["min_success_rate"]),
        ("schema_validity", report.schema_validity, ">=", t["min_schema_validity"]),
        ("mean_tool_recall", report.mean_tool_recall, ">=", t["min_tool_recall"]),
        ("mean_groundedness", report.mean_groundedness, ">=", t["min_mean_groundedness"]),
        ("usd_per_task", report.usd_per_task, "<=", t["max_usd_per_task"]),
        ("p95_latency_ms", report.p95_latency_ms, "<=", t["max_p95_latency_ms"]),
        ("pii_leak_rate", report.pii_leak_rate, "<=", t["max_pii_leak_rate"]),
    ]
    failures: list[str] = []
    for name, actual, op, limit in checks:
        ok = actual >= limit if op == ">=" else actual <= limit
        if not ok:
            failures.append(f"{name} {actual:.6f} {op} {limit}")
    return failures
