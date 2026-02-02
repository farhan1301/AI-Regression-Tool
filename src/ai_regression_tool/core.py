from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


Number = float


@dataclass(frozen=True)
class RegressionResult:
    ok: bool
    regressions: Dict[str, Number]
    improvements: Dict[str, Number]
    unchanged: Dict[str, Number]

    def to_markdown(self) -> str:
        lines: list[str] = []
        lines.append("# AI Regression Report")
        lines.append("")

        def section(title: str, items: Dict[str, Number]) -> None:
            lines.append(f"## {title} ({len(items)})")
            if not items:
                lines.append("- (none)")
            else:
                for k, v in sorted(items.items(), key=lambda kv: kv[0]):
                    sign = "+" if v > 0 else ""
                    lines.append(f"- `{k}`: {sign}{v:.6g}")
            lines.append("")

        section("Regressions", self.regressions)
        section("Improvements", self.improvements)
        section("Unchanged", self.unchanged)

        lines.append("---")
        lines.append(f"**Status:** {'✅ OK' if self.ok else '❌ REGRESSION DETECTED'}")
        return "\n".join(lines).strip() + "\n"


def load_metrics(path: str | Path) -> Dict[str, Number]:
    """Load a flat dict of numeric metrics from a JSON file.

    Expected format examples:
    - {"accuracy": 0.91, "latency_p95_ms": 1200}
    - {"metrics": {"accuracy": 0.91, ...}}  (we'll auto-unpack one level)

    Raises:
      ValueError with a human-readable message for common failure cases.
    """

    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ValueError(f"Metrics file not found: {p}") from e
    except OSError as e:
        raise ValueError(f"Could not read metrics file: {p} ({e})") from e

    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in metrics file: {p} (line {e.lineno}, col {e.colno})") from e

    if isinstance(data, dict) and "metrics" in data and isinstance(data["metrics"], dict):
        data = data["metrics"]

    if not isinstance(data, dict):
        raise ValueError("Metrics JSON must be an object/dict")

    out: Dict[str, Number] = {}
    for k, v in data.items():
        if isinstance(v, (int, float)):
            out[str(k)] = float(v)

    if not out:
        raise ValueError("No numeric metrics found in JSON")

    return out


def compare_metrics(
    baseline: Dict[str, Number],
    candidate: Dict[str, Number],
    *,
    lower_is_better: Iterable[str] = (),
    min_delta: Number = 0.0,
    fail_if_regression: bool = True,
) -> RegressionResult:
    """Compare metric dicts.

    - For most metrics, higher is better.
    - For metrics in lower_is_better, lower is better (e.g. latency, cost).

    A metric is flagged as a regression if it moves in the wrong direction by > min_delta.
    """

    lib = set(lower_is_better)
    keys = set(baseline.keys()) & set(candidate.keys())
    if not keys:
        raise ValueError("No overlapping metrics to compare")

    regressions: Dict[str, Number] = {}
    improvements: Dict[str, Number] = {}
    unchanged: Dict[str, Number] = {}

    for k in sorted(keys):
        b = baseline[k]
        c = candidate[k]
        delta = c - b

        # Define "good" direction
        if k in lib:
            # lower is better: negative delta is improvement
            good = delta < -min_delta
            bad = delta > min_delta
        else:
            good = delta > min_delta
            bad = delta < -min_delta

        if bad:
            regressions[k] = delta
        elif good:
            improvements[k] = delta
        else:
            unchanged[k] = delta

    ok = not regressions if fail_if_regression else True
    return RegressionResult(ok=ok, regressions=regressions, improvements=improvements, unchanged=unchanged)
