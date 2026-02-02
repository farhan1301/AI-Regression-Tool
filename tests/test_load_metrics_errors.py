import json
from pathlib import Path

import pytest

from ai_regression_tool.core import load_metrics


def test_load_metrics_missing_file(tmp_path: Path):
    missing = tmp_path / "missing.json"
    with pytest.raises(ValueError) as e:
        load_metrics(missing)
    assert "not found" in str(e.value).lower()


def test_load_metrics_invalid_json(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not: json}", encoding="utf-8")

    with pytest.raises(ValueError) as e:
        load_metrics(p)
    assert "invalid json" in str(e.value).lower()


def test_load_metrics_no_numeric_metrics(tmp_path: Path):
    p = tmp_path / "non_numeric.json"
    p.write_text(json.dumps({"a": "x", "b": [1, 2, 3]}), encoding="utf-8")

    with pytest.raises(ValueError) as e:
        load_metrics(p)
    assert "no numeric metrics" in str(e.value).lower()
