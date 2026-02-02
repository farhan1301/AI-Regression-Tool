from __future__ import annotations

from typing import Any, Dict


def flatten_numeric(obj: Any, prefix: str = "") -> Dict[str, float]:
    """Flatten nested JSON and return numeric leaves as dot-keys.

    This is intentionally heuristic so it can work across different LangSmith export shapes.
    """

    out: Dict[str, float] = {}

    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(flatten_numeric(v, key))
        return out

    if isinstance(obj, list):
        # Skip lists of dicts by default (too noisy) unless they contain numbers directly.
        # If list has numbers, we keep basic aggregates.
        nums = [x for x in obj if isinstance(x, (int, float))]
        if nums:
            out[prefix + ".min"] = float(min(nums))
            out[prefix + ".max"] = float(max(nums))
            out[prefix + ".mean"] = float(sum(nums) / len(nums))
        return out

    if isinstance(obj, (int, float)):
        if prefix:
            out[prefix] = float(obj)
        return out

    return out


def extract_langsmith_metrics(data: Any) -> Dict[str, float]:
    """Attempt to extract a usable metric dict from a LangSmith JSON export.

    Strategy (best-effort):
    1) If there is a top-level `metrics` object, flatten it.
    2) Else, flatten a likely summary section (`summary`, `results`, `evaluation`, etc.).
    3) Else, flatten the whole payload and filter by common metric substrings.
    """

    if isinstance(data, dict) and isinstance(data.get("metrics"), dict):
        return {k: v for k, v in flatten_numeric(data["metrics"]).items()}

    if isinstance(data, dict):
        for key in ("summary", "results", "evaluation", "eval", "aggregate", "aggregates"):
            if key in data and isinstance(data[key], (dict, list)):
                m = flatten_numeric(data[key])
                if m:
                    return m

    flat = flatten_numeric(data)
    # Keep only things that look like metrics.
    keep = (
        "accuracy",
        "f1",
        "auc",
        "precision",
        "recall",
        "pass",
        "ground",
        "faith",
        "context",
        "latency",
        "cost",
        "token",
        "p95",
        "p99",
    )
    filtered = {k: v for k, v in flat.items() if any(s in k.lower() for s in keep)}
    return filtered or flat
