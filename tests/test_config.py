from ai_regression_tool.config import load_config


def test_default_config_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(None)
    assert cfg.metrics


def test_load_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "ai-regression.yml").write_text(
        """
metrics:
  - key: groundedness
    direction: higher
    abs_threshold: 0.01
    pct_threshold: 0
    severity: fail
""".strip(),
        encoding="utf-8",
    )
    cfg = load_config(None)
    assert cfg.metrics[0].key == "groundedness"
    assert cfg.metrics[0].abs_threshold == 0.01
