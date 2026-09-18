"""CI quality/cost gate for the FastPay exception copilot."""

from __future__ import annotations

from agent_trace_eval.runner import gate_failures, run_suite


def test_quality_and_cost_gate(tmp_path):
    report = run_suite(out_dir=tmp_path)
    failures = gate_failures(report)
    assert not failures, "CI gate failed:\n" + "\n".join(failures)
    assert report.task_count == 26
    assert report.success_rate >= 0.90
    assert report.usd_per_task <= 0.01
    assert (tmp_path / "trace.html").exists()
    assert (tmp_path / "spans.json").exists()
