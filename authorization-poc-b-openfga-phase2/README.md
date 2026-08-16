# POC-B Phase 2 — OpenFGA

## Purpose

POC-B Phase 2 evaluates OpenFGA using the same Phase-1 dataset and
authorization semantics so that all authorization engines can later be
benchmarked against the same workload.

Dataset:

- 50,000 users
- 20,000 resources
- 100 organizations
- 1,000 departments
- 5,000 teams
- 500 applications
- deterministic seed: `42`
- 365,596 relationship tuples

The Phase-1 dataset generator remains the source of truth for the dataset.

---

## Architecture

```text
Application / Postman / Benchmark Client
                |
                v
             OpenFGA
                |
                v
            PostgreSQL
```

OpenFGA manages:

- authorization models
- relationship tuples
- authorization decisions

---

# Setup

## 1. Prerequisites

Install:

- Docker Desktop
- Python 3.11+
- Postman

Verify:

```powershell
docker version
docker compose version
python --version
```

---

## 2. Build the OpenFGA image

The project uses a pinned OpenFGA version and builds a local image for
reproducible runs.

From the project root:

```powershell
docker compose build --no-cache
```

Expected image:

```text
authorization-poc-b-phase2-openfga:1.18.1
```

---

## 3. Start PostgreSQL and OpenFGA

```powershell
docker compose up -d
```

Check:

```powershell
docker compose ps
```

Expected:

```text
pocb2-postgres   Up (healthy)
pocb2-migrate    Exited (0)
pocb2-openfga    Up (healthy)
```

The migration container must complete successfully before the OpenFGA
server is ready.

---

## 4. Verify OpenFGA (poc-2-openFGA-phase-2 : folder name)

Use the Postman request:

```text
00 - Health
```

or:

```text
http://localhost:8080/health
```

---

# Create the baseline authorization model

## 5. Import Postman

Import:

```text
postman/rbac-abac.postman_environment.json
```

Select the imported environment.

Then import:

```text
postman/rbac-abac.postman_collection.json
```

---

## 6. Create the store and baseline model

Run these requests:

```text
00 - Health
01 - Create Store
02 - Create Exact Phase-1 Model
```

The collection stores the returned IDs in:

```text
{{storeId}}
{{modelId}}
```

The authorization model must exist before relationship tuples can be written.

---

# Load the Phase-1 dataset

## 7. Generate the dataset

The Phase-1 generator is the source of truth.

The standard dataset can be generated with:

```powershell
python scripts\generate_tuples.py `
  --seed 42 `
  --users 50000 `
  --resources 20000 `
  --orgs 100 `
  --departments 1000 `
  --teams 5000 `
  --applications 500 `
  --output data\tuples.jsonl `
  --attributes-output data\attributes.json
```

Outputs:

```text
data/tuples.jsonl
data/attributes.json
```

---

## 8. Load all relationship tuples

The standard dataset contains:

```text
365,596 tuples
```

Use the bulk loader:

```powershell
python scripts\load_phase1_tuples.py `
  --store-id "<STORE_ID>" `
  --model-id "<MODEL_ID>" `
  --tuples data\tuples.jsonl `
  --batch-size 100
```

Expected completion:

```text
total_written=365596
```

The bulk loader is used because the dataset contains hundreds of thousands
of tuples and should be loaded programmatically rather than through manual
Postman requests.

---

# Verify the baseline

## 9. Run the baseline Check

After the full dataset has loaded, run:

```text
04 - Check Exact Phase-1 Relationship
```

This verifies that the loaded relationship graph is evaluated by the
baseline OpenFGA model.

---

# Phase-2 experiments

The Phase-2 experiments evaluate additional OpenFGA capabilities against the
same domain and identifiers.

## 10. Conditions

Run:

```text
05 - Create Condition Model
06 - Write Conditional Grant
07 - Condition Check - Valid
08 - Condition Check - Expired
```

The experiment uses a temporary authorization grant with:

```text
grant_time
grant_duration
current_time
```

The valid request should be allowed and the expired request should be denied.

Purpose:

Evaluate conditional and time-dependent authorization.

---

## 11. Contextual Tuples

Run:

```text
09 - Create Contextual Tuple Model
10 - Contextual Tuple Check
```

The relationship is supplied as request context instead of being stored as a
normal persistent tuple.

Purpose:

Evaluate request-scoped authorization relationships.

---

## 12. BatchCheck

Run:

```text
11 - BatchCheck
```

Purpose:

Measure multiple authorization checks in a single API request.

For benchmarks record both:

```text
HTTP requests/sec
logical authorization checks/sec
```

---

## 13. ListObjects

Run:

```text
12 - ListObjects
```

Purpose:

Evaluate reverse authorization queries such as:

```text
Which resources can this user access?
```

Keep ListObjects measurements separate from normal Check measurements.

---

## 14. Consistency

Run:

```text
13 - Check - Minimize Latency
14 - Check - Higher Consistency
```

Purpose:

Compare authorization behavior and latency under the two consistency modes.

Use identical workloads when comparing the modes.

---

# Benchmark methodology

The same dataset and workload methodology will later be used by:

```text
POC-A — OPA + Rego
POC-B — OpenFGA
POC-C — OpenFGA + OPA/Rego
```

Keep these constant:

- dataset
- user identifiers
- resource identifiers
- attributes
- request seed
- workload distribution
- concurrency
- benchmark machine
- benchmark duration

Measure:

```text
P50
P95
P99
P99.9
throughput
error rate
CPU
memory
network
PostgreSQL CPU
PostgreSQL memory
datastore size
```

OpenFGA-specific measurements:

```text
Check
BatchCheck
ListObjects
Condition Check
Contextual Tuple Check
MINIMIZE_LATENCY
HIGHER_CONSISTENCY
```

---

# Reset the local environment

To completely recreate the local Phase-2 environment:

```powershell
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

After a reset:

1. verify OpenFGA health
2. create a new store
3. create the baseline authorization model
4. load the dataset again

---

# Project structure

```text
authorization-poc-b-openfga-phase2/
│
├── README.md
├── docker-compose.yml
│
├── docker/
│   └── Dockerfile.openfga
│
├── model/
│   └── phase1-model.json
│
├── data/
│   ├── tuples.jsonl
│   └── attributes.json
│
├── scripts/
│   ├── generate_tuples.py
│   └── load_phase1_tuples.py
│
├── benchmarks/
├── tests/
└── docs/
```

---

# Phase-2 objectives

By the end of Phase 2, determine:

1. How OpenFGA scales with the Phase-1 relationship dataset.
2. Whether Conditions are sufficient for conditional authorization.
3. When Contextual Tuples are preferable to persisted relationships.
4. The throughput benefit of BatchCheck.
5. The behavior and scalability of ListObjects.
6. The latency/freshness trade-off between consistency modes.
7. Which authorization responsibilities should remain in OpenFGA.
8. Which requirements should be evaluated by OPA/Rego in POC-C.
