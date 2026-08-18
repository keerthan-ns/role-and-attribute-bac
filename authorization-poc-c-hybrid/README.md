# POC-C — Hybrid OpenFGA + OPA/Rego

## Purpose

POC-C evaluates a hybrid authorization design in a completely isolated
runtime:

- OpenFGA — relationship authorization
- OPA/Rego — attribute/context policy evaluation
- Hybrid Gateway — combines the two decisions

POC-C has its own OpenFGA container, PostgreSQL database/volume, OPA container,
Docker network and gateway. It does not use POC-B's runtime resources.

## Isolation

| Component | POC-C |
|---|---|
| PostgreSQL | `pocc-postgres` |
| PostgreSQL host port | `5438` |
| PostgreSQL volume | `authorization-poc-c-postgres-data` |
| OpenFGA | `pocc-openfga` |
| OpenFGA HTTP | `8091` |
| OpenFGA gRPC | `8092` |
| OpenFGA Playground | `3001` |
| OPA | `pocc-opa` |
| OPA HTTP | `8182` |
| Hybrid Gateway | `pocc-gateway` |
| Gateway HTTP | `8090` |
| Docker network | `authorization-poc-c-network` |

OpenFGA's current Docker/PostgreSQL setup uses a PostgreSQL datastore,
`migrate`, and then `run`; this POC follows that structure with isolated
names and ports. citeturn301312search0turn301312search5

OPA is run from the official image in server mode on HTTP 8181 inside the
container; this POC exposes it as host port 8182. citeturn301312search2turn301312search3

## Pinned versions

- OpenFGA: `v1.18.1`
- OPA: `1.18.2`
- PostgreSQL: `17`

## Prerequisites

Install Docker Desktop, Python 3.11+ and Postman.

```powershell
docker version
docker compose version
python --version
```

## 1. Build the isolated images

```powershell
docker compose build --no-cache
```

Images:

```text
authorization-poc-c-openfga:1.18.1
authorization-poc-c-opa:1.18.2
authorization-poc-c-gateway:1.0
```

## 2. Start the POC-C stack

```powershell
docker compose up -d
```

Check:

```powershell
docker compose ps
```

Expected:

```text
pocc-postgres   Up (healthy)
pocc-migrate    Exited (0)
pocc-openfga    Up
pocc-opa        Up
pocc-gateway    Up
```

## 3. Import Postman

Import:

```text
postman/POC-C-Hybrid.postman_environment.json
postman/POC-C-Hybrid.postman_collection.json
```

Select `POC-C Hybrid Local`.

Run:

```text
00 - OpenFGA Health
01 - OPA Health
02 - Gateway Health
03 - Create OpenFGA Store
04 - Create Phase-1 OpenFGA Model
```

The collection stores `storeId` and `modelId` automatically.


### Optional one-command bootstrap

The bundle also contains:

```text
scripts/bootstrap.ps1
```

This is a convenience script that automates the same setup sequence:
health checks, store/model creation, tuple loading, and gateway configuration.

It is **not required**. The documented Postman + tuple-loader workflow above
is the canonical step-by-step setup and should be used when you want each
step to be visible and controlled individually.


## 4. Load the same Phase-1 dataset

The bundle contains the same deterministic Phase-1 generator semantics and a
365,596-tuple dataset:

```text
data/tuples.jsonl
data/attributes.json
scripts/generate_tuples.py
```

Load the relationship tuples into the POC-C OpenFGA instance:

```powershell
python scripts\load_phase1_tuples.py `
  --base-url http://localhost:8091 `
  --store-id "<STORE_ID>" `
  --model-id "<MODEL_ID>" `
  --tuples data\tuples.jsonl `
  --batch-size 100
```

Expected:

```text
total_written=365596
```

## 5. Functional hybrid flow

The gateway request is:

```text
client
  -> gateway
  -> OpenFGA Check
  -> relationship_allowed
  -> OPA/Rego decision
  -> final ALLOW/DENY
```

The final decision is:

```text
OpenFGA ALLOW AND OPA ALLOW = ALLOW
otherwise = DENY
```

The gateway reads subject/resource attributes from `data/attributes.json`.
This keeps the POC self-contained; it is not intended to represent a
production attribute source.

Run Postman:

```text
05 - OpenFGA Baseline Check
06 - OPA Direct Decision
07 - Hybrid Authorization
```

For request `07`, use the generated `{{storeId}}` and `{{modelId}}`.

## 6. Benchmarking

The benchmark compares three paths:

```text
openfga
opa
hybrid
```

Direct OpenFGA is the relationship-engine baseline.
Direct OPA is the policy-engine baseline.
Hybrid is the end-to-end gateway path.

See:

```text
benchmarks/README.md
```

Example:

```powershell
python benchmarks\benchmark.py `
  --scenario openfga `
  --requests 10000 `
  --warmup 500 `
  --concurrency 32 `
  --store-id "<STORE_ID>" `
  --model-id "<MODEL_ID>"
```

```powershell
python benchmarks\benchmark.py `
  --scenario opa `
  --requests 10000 `
  --warmup 500 `
  --concurrency 32
```

```powershell
python benchmarks\benchmark.py `
  --scenario hybrid `
  --requests 10000 `
  --warmup 500 `
  --concurrency 32 `
  --store-id "<STORE_ID>" `
  --model-id "<MODEL_ID>"
```

Recommended sweep:

```text
1, 4, 8, 16, 32, 64, 128, 256
```

Record P50/P95/P99/P99.9, throughput, errors and Docker resource usage.

During benchmark runs:

```powershell
docker stats pocc-openfga pocc-postgres pocc-opa pocc-gateway
```

## 7. Reset

```powershell
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

Then create a new store/model and reload the dataset.

## Project structure

```text
authorization-poc-c-hybrid/
├── README.md
├── docker-compose.yml
├── docker/
│   ├── Dockerfile.openfga
│   └── Dockerfile.opa
├── openfga/model/phase1-aligned-model.json
├── opa/policies/
│   └── policy.rego
├── gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── data/
│   ├── tuples.jsonl
│   └── attributes.json
├── postman/
├── scripts/
├── benchmarks/
└── docs/
```
