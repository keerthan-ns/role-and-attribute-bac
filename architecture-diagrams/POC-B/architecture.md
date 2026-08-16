## Runtime evaluation
```mermaid
flowchart LR

    APP["Application / Client"]

    REQUEST["Authorization Request
    user + relation + object"]

    FGA["OpenFGA
    Authorization Engine"]

    MODEL["Phase-1 Authorization Model"]

    TUPLES["Relationship Tuples
    365,596"]

    DECISION["ALLOW / DENY"]

    APP -->|Check request| REQUEST
    REQUEST --> FGA

    MODEL --> FGA
    TUPLES --> FGA

    FGA -->|Evaluate relationships| DECISION
    DECISION --> APP
```
## Runtime flow
```
Request
   ↓
OpenFGA
   ├── Authorization Model
   └── Relationship Tuples
          ↓
      Relationship evaluation
          ↓
      ALLOW / DENY
```

----------------------------------------------------
# Additional (runtime specific - full flow)
----------------------------------------------------

## Current runtime architecture
```mermaid
flowchart TB

    subgraph CLIENTS["POC-B Clients / Tooling"]
        POSTMAN["Postman\nFunctional API Tests"]
        LOADER["Python Tuple Loader\nload_phase1_tuples.py"]
        BENCH["Python Benchmark Harness"]
        GENERATOR["Phase-1 Dataset Generator"]
    end

    subgraph OPENFGA_STACK["Local OpenFGA Stack"]
        FGA["OpenFGA Server\nHTTP :8080\nDocker container"]

        MODEL["Authorization Model\nPhase-1-aligned model"]

        TUPLES["Relationship Tuples\n365,596"]

        PG["PostgreSQL 17\nOpenFGA Datastore"]
    end

    DATA["data/tuples.jsonl\nattributes.json"]

    GENERATOR -->|"generates"| DATA
    DATA -->|"batch writes"| LOADER
    LOADER -->|"POST /stores/{store}/write"| FGA

    POSTMAN -->|"create store\ncreate model\nCheck"| FGA
    BENCH -->|"Check / benchmark requests"| FGA

    FGA -->|"reads authorization model\nand relationship data"| PG

    MODEL -->|"authorization model"| FGA
    TUPLES -->|"persisted through OpenFGA"| PG

    FGA -->|"ALLOW / DENY"| POSTMAN
    FGA -->|"latency / decision"| BENCH

    classDef client fill:#eef4ff,stroke:#4472c4,color:#111;
    classDef service fill:#eaf6ea,stroke:#3f8f4f,color:#111;
    classDef storage fill:#fff3df,stroke:#c98a00,color:#111;

    class POSTMAN,LOADER,BENCH,GENERATOR client;
    class FGA,MODEL service;
    class PG,TUPLES,DATA storage;
```

### Real data flow
```
generate_tuples.py
        ↓
tuples.jsonl
        ↓
load_phase1_tuples.py
        ↓
OpenFGA /write
        ↓
PostgreSQL
```
### Authorization
```
benchmark/Postman
        ↓
OpenFGA /check
        ↓
PostgreSQL + authorization model
        ↓
ALLOW / DENY
```