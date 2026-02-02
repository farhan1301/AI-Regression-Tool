from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import compare_metrics, load_metrics


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="ai-regression",
        description="Compare two JSON metric files and fail if key metrics regress.",
    )

    p.add_argument("baseline", help="Path to baseline metrics JSON")
    p.add_argument("candidate", help="Path to candidate metrics JSON")

    p.add_argument(
        "--lower-is-better",
        default="latency,cost,token,ms,sec,p95,p99",
        help=(
            "Comma-separated substrings; any metric key containing one of these will be treated as lower-is-better. "
            "Default: latency,cost,token,ms,sec,p95,p99"
        ),
    )

    p.add_argument(
        "--min-delta",
        type=float,
        default=0.0,
        help="Minimum absolute delta required to flag a change (default: 0)",
    )

    p.add_argument(
        "--report",
        default="./ai-regression-report.md",
        help="Where to write the markdown report (default: ./ai-regression-report.md)",
    )

    p.add_argument(
        "--no-fail",
        action="store_true",
        help="Never exit non-zero (useful for local experimentation)",
    )

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)

    baseline = load_metrics(ns.baseline)
    candidate = load_metrics(ns.candidate)

    # Build a lower-is-better set by substring matching.
    lib_substrings = [s.strip() for s in str(ns.lower_is_better).split(",") if s.strip()]
    lower_is_better = {k for k in set(baseline.keys()) & set(candidate.keys()) if any(s in k.lower() for s in lib_substrings)}

    result = compare_metrics(
        baseline,
        candidate,
        lower_is_better=lower_is_better,
        min_delta=float(ns.min_delta),
        fail_if_regression=not bool(ns.no_fail),
    )

    report_path = Path(ns.report)
    report_path.write_text(result.to_markdown(), encoding="utf-8")

    # Print a tiny summary to stdout so CI logs show something useful.
    if result.ok:
        print(f"OK: {len(result.improvements)} improvements, {len(result.regressions)} regressions (report: {report_path})")
        raise SystemExit(0)

    print(f"REGRESSION: {len(result.regressions)} regressions found (report: {report_path})")
    for k, d in sorted(result.regressions.items(), key=lambda kv: kv[0]):
        sign = "+" if d > 0 else ""
        print(f"- {k}: {sign}{d:.6g}")

    raise SystemExit(1)
