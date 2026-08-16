# POC-B — OpenFGA

POC-B evaluates OpenFGA as the relationship-oriented authorization engine using the same conceptual domain and deterministic seed as POC-A.

## Why PostgreSQL

The local POC uses PostgreSQL 17 rather than SQLite because the goal is eventually to evaluate a large tuple/relationship dataset. OpenFGA's current Docker documentation provides a PostgreSQL 17 setup and migration flow.

Official: https://openfga.dev/docs/getting-started/setup-openfga/docker

## What this POC models

- User → organization
- User → department
- User → team
- User → role
- Department → organization
- Team → department
- Resource → organization
- Resource → department
- Resource → team
- Resource → application
- Role-derived viewer/editor/admin access
- inherited access through department/team/organization relationships

The model uses OpenFGA schema 1.1 and domain relationships rather than a generic permission meta-model. This follows OpenFGA's modeling guidance.

## Important ABAC boundary

POC-B keeps attributes such as clearance, location, classification and event zone in `data/attributes.json`. The next stage will explicitly test OpenFGA Conditions and Contextual Tuples against those attributes, instead of forcing every attribute into stored tuples. OpenFGA currently supports Conditions for some ABAC-style cases and Contextual Tuples for request-specific context.

Official docs:
https://openfga.dev/docs/modeling/conditions
https://openfga.dev/docs/interacting/contextual-tuples

## Setup — Windows / PowerShell

Prerequisites: Docker Desktop and Python 3.11+.

### 1. Start OpenFGA + PostgreSQL

```powershell
docker compose up -d
```

Check:

```powershell
Invoke-RestMethod http://localhost:8080/healthz
```

### 2. Bootstrap store + model + tuples

```powershell
.\scripts\bootstrap.ps1
```

This creates an OpenFGA store, converts `model/model.fga` with the official FGA CLI, writes the model, and loads the deterministic tuple dataset.

The OpenFGA Write API currently accepts up to 100 tuple operations per request; the loader therefore writes 100 tuples at a time.

Official: https://openfga.dev/docs/getting-started/update-tuples

### 3. Run a Check

```powershell
python app\openfga_client.py check `
  --store-id $env:FGA_STORE_ID `
  --model-id $env:FGA_MODEL_ID `
  --user user:user-0000000 `
  --relation can_read `
  --object resource:resource-00000000
```

OpenFGA recommends specifying the authorization model ID on relationship queries and writes for predictable behavior and avoiding an extra lookup.

Official: https://openfga.dev/docs/getting-started/immutable-models

### 4. Explore ListObjects

```powershell
python app\openfga_client.py list-objects `
  --store-id $env:FGA_STORE_ID `
  --model-id $env:FGA_MODEL_ID `
  --user user:user-0000000 `
  --relation can_read `
  --type resource
```

This matters for FGAC-like queries because checking one resource and listing all resources are different workloads.

### 5. Run the benchmark

```powershell
python benchmarks\benchmark_check.py `
  --store-id $env:FGA_STORE_ID `
  --model-id $env:FGA_MODEL_ID `
  --requests 10000 `
  --concurrency 32
```

Try concurrency: 1, 4, 8, 16, 32, 64, 128, 256. Record throughput, P50, P95, P99, max and error rate.

### 6. Generate a larger dataset

```powershell
python scripts\generate_tuples.py `
  --users 1000000 `
  --resources 5000000 `
  --orgs 1000 `
  --departments 10000 `
  --teams 50000 `
  --applications 10000 `
  --output data\large-tuples.jsonl `
  --attributes-output data\large-attributes.json
```

Do not commit huge tuple files to Git.

## Benchmark fairness

Use the same hardware, user/resource identifiers, seed, request seed, concurrency levels and latency definitions as POC-A. The internal representation will differ by design; semantic workload must remain equivalent.

## Benchmark roadmap

1. 50K users / 20K resources
2. 1M / 5M
3. concurrency sweep
4. hot user
5. hot resource
6. relationship depth
7. relationship fan-out
8. Check
9. BatchCheck
10. ListObjects
11. relationship update propagation
12. contextual tuples / conditions

OpenFGA supports Batch Check, and its documentation notes batching can reduce network latency.
Official: https://openfga.dev/docs/getting-started/perform-check

## Current POC boundary

This is intentionally the relationship-focused baseline. It does not yet claim OpenFGA alone is the answer for all ABAC/rule requirements. The next benchmark phase will test Conditions, Contextual Tuples and the hybrid architecture.


## Troubleshooting: `Invalid tuple ... role:viewer`

If you see:

```text
Invalid tuple 'resource:...#viewer@role:viewer'
Reason: type 'role' is not an allowed type restriction for 'resource#viewer'
```

the problem is the tuple subject format.

The model declares:

```fga
define viewer: [user, role#member] ...
```

That means the viewer relation accepts either a direct `user` or the
*userset* represented by the members of a `role` object:

```text
role:viewer#member
```

It does NOT accept:

```text
role:viewer
```

The corrected generator included in this package writes role-based
tuples using `role:<name>#member`.

Because the previous bootstrap may already have written hundreds of
thousands of valid tuples before failing, create a NEW OpenFGA store
and bootstrap the corrected dataset from scratch. Do not reuse the
partially populated store for benchmark results.
