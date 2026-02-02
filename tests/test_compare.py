from ai_regression_tool.core import compare_metrics


def test_compare_higher_is_better_regression():
    baseline = {"accuracy": 0.9}
    candidate = {"accuracy": 0.85}

    res = compare_metrics(baseline, candidate, min_delta=0.0)
    assert res.ok is False
    assert "accuracy" in res.regressions


def test_compare_lower_is_better_regression():
    baseline = {"latency_ms": 100.0}
    candidate = {"latency_ms": 120.0}

    res = compare_metrics(baseline, candidate, lower_is_better={"latency_ms"}, min_delta=0.0)
    assert res.ok is False
    assert "latency_ms" in res.regressions


def test_compare_min_delta_ignores_small_changes():
    baseline = {"accuracy": 0.9}
    candidate = {"accuracy": 0.899}

    res = compare_metrics(baseline, candidate, min_delta=0.01)
    assert res.ok is True
    assert "accuracy" in res.unchanged
