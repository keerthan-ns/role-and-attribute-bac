## OpenFGA advanced runtime evaluation
```mermaid
flowchart LR

    APP["Application / Client"]

    REQUEST["Authorization Request
    user + relation + object"]

    CONTEXT["Optional Request Context
    current_time / contextual tuples"]

    FGA["OpenFGA
    Authorization Engine"]

    MODEL["Authorization Model"]

    TUPLES["Persisted Relationship Tuples"]

    CONDITION["Condition Evaluation"]

    RELATION["Relationship Evaluation"]

    DECISION["ALLOW / DENY"]

    APP --> REQUEST
    REQUEST --> FGA

    MODEL --> FGA
    TUPLES --> FGA

    REQUEST -.->|Optional context| CONTEXT
    CONTEXT -.-> FGA

    FGA --> RELATION
    FGA --> CONDITION

    RELATION --> DECISION
    CONDITION --> DECISION

    DECISION --> APP
```

## Runtime concept
```
                    Authorization Request
                            │
                            ▼
                       OpenFGA
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
      Relationship Evaluation       Conditional Evaluation
              │                           │
              │                    request context
              │                    / contextual tuples
              │                           │
              └─────────────┬─────────────┘
                            ▼
                       ALLOW / DENY
```
- The key difference from Phase 1 is therefore not a new service or deployment. It's that the request can use:
```
Phase 1:
relationship evaluation

Phase 2:
relationship evaluation
        +
Conditions
        +
Contextual Tuples
```                       

### Important note 
The phase-2 architecture is designed to support three different authorization models, all of which share the same OpenFGA store. The three models are:
- Baseline / Phase-1 model, which uses the persisted Phase-1 tuples [link](phases/phase1-tuples.md)
- Condition model, which uses a conditional relationship tuple stored in the datastore [link](phases/phase2-conditional-tuple.md)
- Contextual model, which uses contextual tuples provided in the request and does not persist them in the datastore [link](phases/phase2-contextual-tuples.md)

```
                    OpenFGA Server
                         │
                         ▼
                    One Store
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
     Baseline       Condition      Contextual
       Model          Model           Model
```

----------------------------------------------------
# Additional (runtime specific - full flow)
----------------------------------------------------
## Architecture diagram
```
                         SAME OPENFGA STORE
                                │
             ┌──────────────────┼─────────────────┐
             │                  │                 │
             ▼                  ▼                 ▼
      Baseline Model      Condition Model   Contextual Model
             │                  │                 │
             ▼                  ▼                 ▼
     365,596 tuples     conditional tuple    request context
```

## Current runtime architecture
```mermaid
flowchart TB

    subgraph DATASET["Phase-1 Dataset"]
        GENERATOR["generate_tuples.py"]
        TUPLEFILE["data/tuples.jsonl\n365,596 tuples"]
        ATTRS["data/attributes.json"]
        
        GENERATOR --> TUPLEFILE
        GENERATOR --> ATTRS
    end

    subgraph CLIENTS["POC-B Phase 2 Clients"]
        POSTMAN["Postman\nFunctional Experiments"]
        LOADER["load_phase1_tuples.py"]
        BENCH["Benchmark Harness"]
    end

    subgraph LOCAL["Local Docker Environment"]
        FGA["OpenFGA Server\nHTTP :8080"]

        STORE["OpenFGA Store"]

        subgraph MODELS["Authorization Models"]
            BASELINE["Baseline / Phase-1 Model"]
            CONDITION["Condition Model"]
            CONTEXTUAL["Contextual Tuple Model"]
        end

        PG["PostgreSQL 17\nOpenFGA Datastore"]
    end

    %% Dataset loading
    TUPLEFILE -->|"365,596 tuple writes"| LOADER
    LOADER -->|"/write"| FGA

    %% Clients
    POSTMAN -->|"/stores / authorization-models"| FGA
    POSTMAN -->|"/check / /batch-check / /list-objects"| FGA
    BENCH -->|"/check / /batch-check / /list-objects"| FGA

    %% Store/model
    FGA --> STORE

    BASELINE --> STORE
    CONDITION --> STORE
    CONTEXTUAL --> STORE

    STORE <--> PG

    %% Baseline experiment
    BASELINE -.->|"uses persisted\nPhase-1 tuples"| PG

    %% Condition
    CONDITION -.->|"conditional relationship\ntuple stored in datastore"| PG
    POSTMAN -->|"condition context"| CONDITION

    %% Contextual
    CONTEXTUAL -.->|"NO persistent contextual tuple"| FGA
    POSTMAN -->|"contextual_tuples"| CONTEXTUAL
    BENCH -->|"contextual_tuples"| CONTEXTUAL

    %% Responses
    FGA -->|"ALLOW / DENY / objects"| POSTMAN
    FGA -->|"latency / throughput"| BENCH
```

## Batch check flow
```mermaid
flowchart LR

    CLIENT["Benchmark / Postman"]

    BATCH["One HTTP BatchCheck Request"]

    FGA["OpenFGA"]

    C1["Check 1"]
    C2["Check 2"]
    C3["Check 3"]
    CN["... Check N"]

    RESULT["Batch Response"]

    CLIENT --> BATCH
    BATCH --> FGA

    FGA --> C1
    FGA --> C2
    FGA --> C3
    FGA --> CN

    C1 --> RESULT
    C2 --> RESULT
    C3 --> RESULT
    CN --> RESULT

    RESULT --> CLIENT
```

## ListObjects flow
```mermaid
sequenceDiagram
    participant Client as Benchmark / Postman
    participant FGA as OpenFGA
    participant Store as OpenFGA
    participant PG as PostgreSQL

    Client->>FGA: ListObjects(user, can_read, resource)
    FGA->>Store: Evaluate relationships
    Store->>PG: Read authorization data
    PG-->>Store: tuples
    Store-->>FGA: Matching resources
    FGA-->>Client: [resource-1, resource-2, ...]
```

## Overall architecture
```mermaid
flowchart TB

    DATA["Phase-1 Dataset\n50K users / 20K resources\n365,596 tuples"]

    GENERATOR["generate_tuples.py"]
    LOADER["load_phase1_tuples.py"]

    POSTMAN["Postman"]
    BENCH["Benchmark Harness"]

    subgraph OPENFGA["OpenFGA POC Environment"]
        SERVER["OpenFGA Server"]

        subgraph STORE["Single OpenFGA Store"]
            BASE["Baseline Model\nPhase-1 model"]
            COND["Condition Model"]
            CTX["Contextual Tuple Model"]
        end

        PG["PostgreSQL 17"]
    end

    GENERATOR --> DATA
    DATA --> LOADER
    LOADER -->|"Write 365,596 tuples"| SERVER

    POSTMAN -->|"Store / Model management"| SERVER
    POSTMAN -->|"Check / Condition / Context"| SERVER

    BENCH -->|"Check"| SERVER
    BENCH -->|"BatchCheck"| SERVER
    BENCH -->|"ListObjects"| SERVER
    BENCH -->|"Consistency"| SERVER

    SERVER --> STORE
    STORE --> PG

    BASE -.->|"persisted Phase-1 tuples"| PG
    COND -.->|"conditional tuple data"| PG
    CTX -.->|"request-scoped tuples"| SERVER

    SERVER -->|"authorization decisions"| POSTMAN
    SERVER -->|"latency / throughput"| BENCH
```