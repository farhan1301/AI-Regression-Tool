# AI Regression Tool

A small, dependency-light CLI to detect metric regressions between two AI experiment runs.

The goal is to make it trivial to gate changes in CI/CD: if a candidate run regresses on important metrics (accuracy, pass rate, groundedness, latency, cost), fail the build and generate a readable markdown report.

## Install (local)

```bash
python -m pip install -e '.[dev]'
```

## Usage

### Compare two JSON files

```bash
ai-regression baseline.json candidate.json --report ./ai-regression-report.md
```

- Metrics JSON can be either a flat dict:
  - `{ "accuracy": 0.91, "latency_p95_ms": 1200 }`
- Or wrapped one level deep:
  - `{ "metrics": { "accuracy": 0.91, ... } }`

### Treat latency/cost metrics as lower-is-better

By default the CLI treats any metric key containing:
`latency,cost,token,ms,sec,p95,p99` as lower-is-better.

Override it:

```bash
ai-regression baseline.json candidate.json \
  --lower-is-better latency,ms,p95,cost \
  --min-delta 0.01
```

## CI

This repo includes a GitHub Actions workflow that runs tests on Python 3.10–3.12.

## Roadmap (small + practical)

- Support nested metric extraction (e.g., `metrics.latency.p95_ms`).
- Add optional YAML config for metric direction + thresholds.
- Add a `--format json` report for machine consumption.
