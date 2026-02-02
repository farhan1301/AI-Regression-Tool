from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional

import yaml


Direction = Literal["higher", "lower"]
Severity = Literal["fail", "warn"]


@dataclass(frozen=True)
class MetricRule:
    key: str
    direction: Direction = "higher"
    abs_threshold: float = 0.0
    pct_threshold: float = 0.0
    severity: Severity = "fail"


@dataclass(frozen=True)
class Config:
    metrics: List[MetricRule]

    @staticmethod
    def default() -> "Config":
        # Reasonable defaults for AI/RAG and production concerns.
        return Config(
            metrics=[
                MetricRule("accuracy", direction="higher", abs_threshold=0.0, pct_threshold=0.0, severity="fail"),
                MetricRule("pass_rate", direction="higher", abs_threshold=0.0, pct_threshold=0.0, severity="fail"),
                MetricRule("groundedness", direction="higher", abs_threshold=0.0, pct_threshold=0.0, severity="fail"),
                MetricRule("faithfulness", direction="higher", abs_threshold=0.0, pct_threshold=0.0, severity="fail"),
                MetricRule("context_precision", direction="higher", abs_threshold=0.0, pct_threshold=0.0, severity="warn"),
                MetricRule("latency_p95_ms", direction="lower", abs_threshold=0.0, pct_threshold=0.0, severity="warn"),
                MetricRule("cost_per_query", direction="lower", abs_threshold=0.0, pct_threshold=0.0, severity="warn"),
                MetricRule("token_usage", direction="lower", abs_threshold=0.0, pct_threshold=0.0, severity="warn"),
            ]
        )


def _coerce_direction(v: Any) -> Direction:
    s = str(v).strip().lower()
    if s in ("higher", "up", "increase"):
        return "higher"
    if s in ("lower", "down", "decrease"):
        return "lower"
    raise ValueError(f"Invalid metric direction: {v!r} (expected 'higher' or 'lower')")


def _coerce_severity(v: Any) -> Severity:
    s = str(v).strip().lower()
    if s in ("fail", "error"):
        return "fail"
    if s in ("warn", "warning"):
        return "warn"
    raise ValueError(f"Invalid metric severity: {v!r} (expected 'fail' or 'warn')")


def load_config(path: str | Path | None) -> Config:
    """Load config from YAML.

    If path is None:
    - uses ./ai-regression.yml if present
    - otherwise returns Config.default()

    YAML schema (minimal):

    metrics:
      - key: groundedness
        direction: higher|lower
        abs_threshold: 0.01
        pct_threshold: 0.0
        severity: fail|warn
    """

    if path is None:
        default_path = Path("ai-regression.yml")
        if not default_path.exists():
            return Config.default()
        path = default_path

    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ValueError(f"Config file not found: {p}") from e

    try:
        data = yaml.safe_load(raw) or {}
    except Exception as e:
        raise ValueError(f"Invalid YAML in config: {p} ({e})") from e

    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping/object")

    metrics_raw = data.get("metrics")
    if metrics_raw is None:
        return Config.default()
    if not isinstance(metrics_raw, list):
        raise ValueError("Config 'metrics' must be a list")

    rules: List[MetricRule] = []
    for item in metrics_raw:
        if not isinstance(item, dict) or "key" not in item:
            raise ValueError("Each metric rule must be an object with at least 'key'")
        rules.append(
            MetricRule(
                key=str(item["key"]),
                direction=_coerce_direction(item.get("direction", "higher")),
                abs_threshold=float(item.get("abs_threshold", 0.0) or 0.0),
                pct_threshold=float(item.get("pct_threshold", 0.0) or 0.0),
                severity=_coerce_severity(item.get("severity", "fail")),
            )
        )

    if not rules:
        return Config.default()

    return Config(metrics=rules)
