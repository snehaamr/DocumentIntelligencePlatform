"""Render a Jaeger-style waterfall from exported OTel spans (no live SaaS)."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def spans_to_dicts(spans: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for span in spans:
        ctx = span.get_span_context()
        parent = span.parent.span_id if span.parent else 0
        rows.append(
            {
                "trace_id": f"{ctx.trace_id:032x}",
                "span_id": f"{ctx.span_id:016x}",
                "parent_span_id": f"{parent:016x}" if parent else "",
                "name": span.name,
                "kind": span.kind.name,
                "start_ns": span.start_time,
                "end_ns": span.end_time,
                "status": span.status.status_code.name,
                "attributes": {k: _plain(v) for k, v in (span.attributes or {}).items()},
            }
        )
    rows.sort(key=lambda r: r["start_ns"])
    return rows


def _plain(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    return value


def write_json(path: Path, spans: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spans, indent=2, default=str))


def write_html(path: Path, spans: list[dict[str, Any]], title: str = "agent-trace-eval") -> None:
    traces: dict[str, list[dict[str, Any]]] = {}
    for span in spans:
        traces.setdefault(span["trace_id"], []).append(span)
    sections = []
    for trace_id, items in traces.items():
        t0 = min(s["start_ns"] for s in items)
        t1 = max(s["end_ns"] for s in items)
        width = max(t1 - t0, 1)
        rows_html = []
        for span in items:
            left = (span["start_ns"] - t0) / width * 100
            dur = (span["end_ns"] - span["start_ns"]) / 1e6
            w = max((span["end_ns"] - span["start_ns"]) / width * 100, 0.6)
            op = span["attributes"].get("gen_ai.operation.name", "")
            color = {
                "invoke_agent": "#b08600",
                "chat": "#3d8bfd",
                "execute_tool": "#2bb673",
                "retrieval": "#9b59ff",
                "guardrail": "#e5534b",
            }.get(str(op), "#888")
            err = " err" if span["status"] == "ERROR" else ""
            attrs = html.escape(json.dumps(span["attributes"], indent=2, default=str)[:2500])
            rows_html.append(
                f'<div class="row{err}"><div class="label">{html.escape(span["name"])}'
                f'<small>{html.escape(str(op))} · {dur:.2f}ms</small></div>'
                f'<div class="track"><i style="left:{left:.2f}%;width:{w:.2f}%;background:{color}"></i></div>'
                f'<pre>{attrs}</pre></div>'
            )
        sections.append(
            f'<section><h2>trace {trace_id[:16]}… · {len(items)} spans</h2>{"".join(rows_html)}</section>'
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body{{margin:0;background:#1f1f1f;color:#eee;font:13px/1.4 ui-sans-serif,system-ui}}
header{{background:#161616;padding:14px 20px;border-bottom:1px solid #333}}
h1{{margin:0;font-size:16px;color:#f0c14b}}
h2{{font-size:13px;color:#bbb;margin:18px 20px 8px;font-weight:600}}
.legend span{{display:inline-block;margin-right:12px}}
.legend i{{display:inline-block;width:10px;height:10px;margin-right:4px}}
section{{padding:0 20px 24px}}
.row{{margin:0 0 6px;background:#2a2a2a;border-radius:4px;padding:6px 8px}}
.row.err{{outline:1px solid #e5534b}}
.label{{display:flex;justify-content:space-between;gap:12px}}
.label small{{color:#aaa}}
.track{{position:relative;height:16px;background:#111;margin:6px 0;border-radius:2px}}
.track i{{position:absolute;top:3px;height:10px;border-radius:2px;opacity:.95}}
pre{{display:none;max-height:220px;overflow:auto;background:#111;color:#cde;padding:8px}}
.row:hover pre{{display:block}}
.row.err pre{{display:block}}
</style></head>
<body>
<header>
  <h1>Jaeger-style waterfall · {html.escape(title)}</h1>
  <div class="legend">
    <span><i style="background:#b08600"></i>invoke_agent</span>
    <span><i style="background:#3d8bfd"></i>chat</span>
    <span><i style="background:#2bb673"></i>execute_tool</span>
    <span><i style="background:#9b59ff"></i>retrieval</span>
    <span><i style="background:#e5534b"></i>guardrail</span>
  </div>
</header>
{''.join(sections) or '<p style="padding:20px">No spans.</p>'}
</body></html>
"""
    )
