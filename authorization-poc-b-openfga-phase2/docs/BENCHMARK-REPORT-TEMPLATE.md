# POC-B Phase 2 Benchmark Report

## Environment

| Item | Value |
|---|---|
| OpenFGA version | |
| PostgreSQL version | |
| Docker Desktop version | |
| Host CPU | |
| Host RAM | |
| OS | |
| Dataset users | 50,000 |
| Dataset resources | 20,000 |
| Tuple count | 365,596 |
| Seed | 42 |

## Baseline Check

| Concurrency | Throughput | P50 | P95 | P99 | P99.9 | Errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | | | | | | |
| 4 | | | | | | |
| 8 | | | | | | |
| 16 | | | | | | |
| 32 | | | | | | |
| 64 | | | | | | |
| 128 | | | | | | |
| 256 | | | | | | |

## Condition Check

Same table.

## Contextual Tuple Check

Same table.

## BatchCheck

| Batch size | Concurrency | Logical checks/sec | HTTP req/sec | P50 | P95 | P99 |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | | | | | | |
| 10 | | | | | | |
| 25 | | | | | | |
| 50 | | | | | | |

## ListObjects

Record separately:

- average
- P50
- P95
- P99
- response object count
- throughput

## Consistency

Compare:

- MINIMIZE_LATENCY
- HIGHER_CONSISTENCY

## Infrastructure

Record OpenFGA and PostgreSQL:

- CPU
- memory
- network
- disk I/O

## Observations

Document:

- saturation point
- latency inflection point
- error onset
- cache effects
- datastore pressure
- relationship depth/fan-out observations
