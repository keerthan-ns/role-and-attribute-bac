# POC-A — OPA + Rego

This POC evaluates OPA/Rego for a large-scale authorization workload.
It deliberately uses a single authorization decision endpoint and a
shared synthetic dataset so the same workload can later be used for
OpenFGA and the hybrid POC.

## Current baseline

- OPA Docker image: `openpolicyagent/opa:1.18.2`
- Dev dataset: 50,000 users + 20,000 resources
- Deterministic seed: 42
- Policies: RBAC + ABAC + contextual constraints
- Decision endpoint: `POST /v1/data/authz/decision`

The OPA version is pinned instead of using `latest`, because reproducible
benchmarks need a fixed version. The official OPA Docker documentation
recommends explicit version tags for production-style use. See:
https://www.openpolicyagent.org/docs/deploy/docker

## 1. Prerequisites

- Docker Desktop / Docker Engine
- Python 3.11+ (3.12/3.13 also fine)
- PowerShell, Bash, or equivalent shell

## 2. Start OPA

From this directory:

```bash
docker compose up -d
```

Check:

```bash
curl http://localhost:8181/health
```

Windows PowerShell:

```powershell
Invoke-RestMethod http://localhost:8181/health
```

## 3. Run policy tests

Using the OPA CLI locally is preferred for development:

`NOTE:` only if path is not set
```bash
set PATH=%PATH%;S:\tools\opa
```

```bash
opa test opa/policies tests -v
```

If you do not have OPA installed locally, use Docker:

```bash
docker run --rm `
  -v "${PWD}:/work" `
  openpolicyagent/opa:1.18.2 `
  test /work/opa/policies /work/tests -v
```

## 4. Inspect the policy

```bash
curl http://localhost:8181/v1/policies
```

PowerShell:

```powershell
Invoke-RestMethod http://localhost:8181/v1/policies
```

## 5. Make a decision request

Example:

```json
{
  "input": {
    "subject": {
      "id": "user-demo",
      "roles": ["admin"],
      "org_id": "org-0001",
      "department_id": "dept-00001",
      "clearance": 5,
      "event_zone": "ZONE-A",
      "location": "DELHI"
    },
    "resource": {
      "id": "resource-demo",
      "type": "document",
      "org_id": "org-0001",
      "department_id": "dept-00002",
      "classification": 4,
      "event_zone": "ZONE-C",
      "allowed_location": null
    },
    "action": "read",
    "context": {
      "location": "DELHI"
    }
  }
}
```

Use:

```bash
curl -X POST http://localhost:8181/v1/data/authz/decision \
  -H "Content-Type: application/json" \
  -d @request.json
```

## 6. Run the benchmark

The included benchmark sends concurrent HTTP requests to OPA and reports:

- throughput
- average latency
- P50
- P95
- P99
- min/max
- errors

Example:

```bash
python benchmarks/benchmark_opa.py --requests 10000 --concurrency 32
```

## 7. Generate a larger dataset

Do NOT commit multi-gigabyte generated JSON into git.

Generate it locally:

```bash
python scripts/generate_dataset.py \
  --seed 42 \
  --users 1000000 \
  --resources 5000000 \
  --orgs 1000 \
  --departments 10000 \
  --teams 50000 \
  --output opa/data/large-data.json
```

Then modify `docker-compose.yml` to mount/use that dataset.

Important: this JSON-replication approach is intentionally only the
first POC. One of the major Phase-1 research questions is whether a
single OPA instance should hold this much authorization data in memory,
or whether external data / relationship storage is needed.

## 8. First benchmark sequence

Run these in order:

### A. Policy-only baseline

Small input, tiny data.

Goal: measure raw Rego evaluation overhead.

### B. Development dataset

50K users, 20K resources.

Goal: realistic local POC.

### C. 1M users / 5M resources

Goal: identify memory and policy/data-loading limits.

### D. Concurrency sweep

Try:

```text
1
4
8
16
32
64
128
256
```

Record P50/P95/P99 and throughput.

### E. Complexity sweep

Compare:

- simple RBAC
- RBAC + department
- RBAC + ABAC
- complex contextual policy

Do not mix results from different configurations.

## 9. What this POC is NOT yet

This is not the final authorization framework.

We still need:

- production policy control plane
- signed bundles
- policy versioning
- audit pipeline
- identity integration
- distributed OPA deployment
- FGAC/data filtering
- relationship graph evaluation
- OpenFGA comparison
- hybrid comparison

Those are deliberate later phases.

## Architecture hypothesis

For the real system, the current hypothesis is:

```text
Policy UI
   |
Policy Management / Control Plane
   |
Signed policy/data bundle
   |
+--+---------+---------+
|            |         |
OPA-1       OPA-2     OPA-N
|            |         |
Service     Service   Service
```

The POC exists to test whether that hypothesis survives large-scale
data and concurrency.

