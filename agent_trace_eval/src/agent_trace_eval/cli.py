"""CLI: run the labeled suite or print the last report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_trace_eval.eval import markdown_table
from agent_trace_eval.runner import gate_failures, run_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-trace-eval")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="Pick up labeled tasks and score them")
    run_p.add_argument("--out", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)
    if args.cmd == "run":
        report = run_suite(out_dir=args.out)
        print(markdown_table(report))
        failures = gate_failures(report)
        if failures:
            print("GATE FAIL:", "; ".join(failures), file=sys.stderr)
            return 1
        print("GATE PASS")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
