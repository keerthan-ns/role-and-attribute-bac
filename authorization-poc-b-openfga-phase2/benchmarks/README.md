# POC-B Phase 2 — Benchmarking

The benchmark layer is designed to use the same 365,596-tuple OpenFGA store
that was loaded for the functional POC.

## Scenarios

- `check` — baseline `Check` using the Phase-1 model
- `condition` — time-based conditional `Check`
- `contextual` — request-scoped contextual tuple `Check`
- `batch-check` — multiple logical checks in one HTTP request
- `list-objects` — reverse authorization query
- `consistency-min` — `MINIMIZE_LATENCY`
- `consistency-high` — `HIGHER_CONSISTENCY`

## Required IDs

Set these environment variables in the shell used for benchmarking:

```powershell
$env:STORE_ID = "<store-id>"
$env:BASELINE_MODEL_ID = "<phase-1-model-id>"
$env:CONDITION_MODEL_ID = "<condition-model-id>"
$env:CONTEXTUAL_MODEL_ID = "<contextual-model-id>"
```

Alternatively pass the IDs directly to the benchmark command.

## First benchmark: baseline Check

Use a warm-up so connection establishment and first-request effects are not
included in the measured sample:

```powershell
python benchmarks\benchmark.py `
  --scenario check `
  --requests 10000 `
  --warmup 500 `
  --concurrency 32
```

The benchmark uses the exact Phase-1 user/resource identifiers passed through
`--user` and `--resource`.

## Condition

```powershell
python benchmarks\benchmark.py `
  --scenario condition `
  --requests 10000 `
  --warmup 500 `
  --concurrency 32
```

The default condition context is 12:30 UTC, which is inside the one-hour
grant configured for the functional experiment.

To benchmark a different context, use:

```text
--condition-current-time 2026-08-16T12:30:00Z
```

## Contextual tuples

```powershell
python benchmarks\benchmark.py `
  --scenario contextual `
  --requests 10000 `
  --warmup 500 `
  --concurrency 32
```

The contextual relationship is included on every request and is not persisted.

## BatchCheck

```powershell
python benchmarks\benchmark.py `
  --scenario batch-check `
  --requests 10000 `
  --warmup 100 `
  --concurrency 32 `
  --batch-size 50
```

`--requests` means logical authorization checks.

For example:

```text
requests = 10,000
batch-size = 50
```

means:

```text
10,000 logical checks
200 HTTP requests
```

Report both:

```text
logical_checks_per_second
http_requests_per_second
```

## ListObjects

```powershell
python benchmarks\benchmark.py `
  --scenario list-objects `
  --requests 1000 `
  --warmup 50 `
  --concurrency 16
```

ListObjects is intentionally benchmarked separately because it returns a set
of authorized objects rather than a single boolean.

## Consistency

```powershell
python benchmarks\benchmark.py `
  --scenario consistency-min `
  --requests 10000 `
  --warmup 500 `
  --concurrency 32
```

and:

```powershell
python benchmarks\benchmark.py `
  --scenario consistency-high `
  --requests 10000 `
  --warmup 500 `
  --concurrency 32
```

Run these under the same workload and concurrency.

Note: a meaningful cache/consistency comparison requires the OpenFGA server
cache configuration to be explicitly enabled/configured. The functional
POC should first establish the baseline without introducing another variable.

## Standard concurrency sweep

Run:

```powershell
python benchmarks\run_sweep.py `
  --requests 10000 `
  --warmup 500 `
  --concurrency 1 4 8 16 32 64 128 256
```

This runs all scenarios by default.

To reduce runtime:

```powershell
python benchmarks\run_sweep.py `
  --scenarios check condition contextual batch-check `
  --requests 10000 `
  --warmup 500 `
  --concurrency 1 8 32 128 `
  --batch-size 50
```

## Results

Each run creates a JSON result under:

```text
benchmarks/results/
```

Example:

```text
check-r10000-c32.json
batch-check-r10000-c32-b50.json
condition-r10000-c32.json
```

Summarize all results:

```powershell
python benchmarks\summarize_results.py
```

Output:

```text
benchmarks/results/summary.csv
```

## Metrics

Each result contains:

- requests
- HTTP requests
- concurrency
- successful HTTP requests
- errors
- wall-clock duration
- HTTP requests/sec
- logical checks/sec
- average latency
- P50
- P95
- P99
- P99.9
- maximum latency
- allowed true/false counts

## Benchmark rules

For POC-A, POC-B and POC-C use:

- the same dataset
- the same identifiers
- the same request seed
- the same workload distribution
- the same concurrency sweep
- the same number of requests
- the same warm-up count
- the same machine

Do not compare one engine with warm-up and another without warm-up.

Do not compare one engine's `ListObjects` latency directly with another
engine's boolean `Check` latency.

For BatchCheck always compare logical checks/sec.

## Infrastructure telemetry

The benchmark harness measures application-level latency only.

During the benchmark also capture Docker resource usage for:

```text
pocb2-openfga
pocb2-postgres
```

Use a separate terminal:

```powershell
docker stats pocb2-openfga pocb2-postgres
```

Record:

- CPU %
- memory usage
- memory %
- network I/O
- block I/O

Keep infrastructure observations alongside the JSON result files.

## Recommended first benchmark campaign

Start with:

```text
requests = 10,000
warmup = 500
concurrency = 1, 4, 8, 16, 32, 64, 128, 256
```

Then repeat the most interesting scenarios with:

```text
requests = 100,000
```

After that, scale the dataset and rerun the same matrix.

Do not change the benchmark workload while comparing dataset sizes.
