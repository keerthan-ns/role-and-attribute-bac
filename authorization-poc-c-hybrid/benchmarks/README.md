# POC-C Hybrid Benchmarking

Scenarios:

- `openfga` — direct OpenFGA Check
- `opa` — direct OPA decision
- `hybrid` — gateway -> OpenFGA -> OPA -> final decision

Example:

```powershell
python benchmarks\benchmark.py --scenario openfga --requests 10000 --warmup 500 --concurrency 32 --store-id "<STORE_ID>" --model-id "<MODEL_ID>"
python benchmarks\benchmark.py --scenario opa --requests 10000 --warmup 500 --concurrency 32
python benchmarks\benchmark.py --scenario hybrid --requests 10000 --warmup 500 --concurrency 32
```

Use the same workload, request count, warmup and concurrency as POC-A and POC-B.
Do not treat hybrid latency as engine-only latency: it includes gateway and two
upstream HTTP calls.
