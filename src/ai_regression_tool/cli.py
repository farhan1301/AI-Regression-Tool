from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .core import compare_metrics, load_metrics


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="ai-regression",
        description="Compare two JSON metric files and fail if key metrics regress.",
    )

    p.add_argument("baseline", help="Path to baseline metrics JSON")
    p.add_argument("candidate", help="Path to candidate metrics JSON")

    p.add_argument(
        "--format",
        default="auto",
        choices=["auto", "flat", "langsmith"],
        help="Input format (default: auto). Use 'langsmith' for LangSmith exports.",
    )

    p.add_argument(
        "--config",
        default=None,
        help="Path to ai-regression.yml (default: use ./ai-regression.yml if present)",
    )

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

    cfg = load_config(ns.config)

    baseline = load_metrics(ns.baseline, fmt=ns.format)
    candidate = load_metrics(ns.candidate, fmt=ns.format)

    # Decide per-metric direction using config rules.
    rules_by_key = {r.key: r for r in cfg.metrics}
    overlap = set(baseline.keys()) & set(candidate.keys())

    # If config keys are "short" (e.g. groundedness) and inputs are dotted paths,
    # allow suffix match. This makes LangSmith flattening usable without perfect mapping.
    def match_rule(metric_key: str):
        if metric_key in rules_by_key:
            return rules_by_key[metric_key]
        for k, r in rules_by_key.items():
            if metric_key.lower().endswith(k.lower()):
                return r
        return None

    lower_is_better = set()
    min_delta = float(ns.min_delta)
    fail_if_regression = not bool(ns.no_fail)

    # Apply per-metric thresholds by folding them into min_delta at compare-time.
    # For now, we use the max(abs_threshold, pct_threshold * |baseline|).
    # We compute a per-metric delta and do classification here.
    regressions = {}
    improvements = {}
    unchanged = {}

    for key in sorted(overlap):
        b = float(baseline[key])
        c = float(candidate[key])
        delta = c - b

        rule = match_rule(key)
        direction = (rule.direction if rule else None) or ("lower" if any(s in key.lower() for s in str(ns.lower_is_better).split(",")) else "higher")
        severity = (rule.severity if rule else "fail")
        threshold = 0.0
        if rule:
            threshold = max(float(rule.abs_threshold), abs(b) * float(rule.pct_threshold))
        threshold = max(threshold, min_delta)

        if direction == "lower":
            good = delta < -threshold
            bad = delta > threshold
        else:
            good = delta > threshold
            bad = delta < -threshold

        if bad:
            regressions[key] = (delta, severity)
        elif good:
            improvements[key] = delta
        else:
            unchanged[key] = delta

    # Build core RegressionResult for markdown + exit code
    from .core import RegressionResult

    result = RegressionResult(
        ok=(not any(sev == "fail" for _, sev in regressions.values())) if fail_if_regression else True,
        regressions={k: d for k, (d, _) in regressions.items()},
        improvements=improvements,
        unchanged=unchanged,
    )

    report_path = Path(ns.report)
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(result.to_markdown(), encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"Failed to write report to {report_path}: {e}")

    # Print a tiny summary to stdout so CI logs show something useful.
    # GitHub Actions summary support
    try:
        import os

        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            Path(summary_path).write_text(result.to_markdown(), encoding="utf-8")
    except OSError:
        # If we can't write the summary, don't fail the whole run.
        pass

    if result.ok:
        print(f"OK: {len(result.improvements)} improvements, {len(result.regressions)} regressions (report: {report_path})")
        raise SystemExit(0)

    print(f"REGRESSION: {len(result.regressions)} regressions found (report: {report_path})")
    for k, d in sorted(result.regressions.items(), key=lambda kv: kv[0]):
        sign = "+" if d > 0 else ""
        print(f"- {k}: {sign}{d:.6g}")

    raise SystemExit(1)
