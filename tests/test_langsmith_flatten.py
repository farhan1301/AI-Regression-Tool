from ai_regression_tool.langsmith import flatten_numeric, extract_langsmith_metrics


def test_flatten_numeric_basic():
    data = {"a": {"b": 1, "c": 2.5}, "d": "x"}
    flat = flatten_numeric(data)
    assert flat["a.b"] == 1.0
    assert flat["a.c"] == 2.5


def test_extract_langsmith_prefers_metrics_key():
    payload = {"metrics": {"accuracy": 0.9, "latency_ms": 100}}
    m = extract_langsmith_metrics(payload)
    assert m["accuracy"] == 0.9
