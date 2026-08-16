## Runtime/Deployment Architecture
```mermaid
flowchart TB

    %% =========================
    %% ADMIN / CONTROL PLANE
    %% =========================

    subgraph CONTROL["Authorization Control Plane"]
        UI["React + ShadCN\nAuthorization Administration UI"]

        API["Authorization Management API\nModel / Tuple / Policy Management"]

        MODEL_REPO["Authorization Model Repository\nmodel.fga / versioned models"]

        MODEL_VALIDATOR["Model Validation / Tests"]

        FGA_MODEL["OpenFGA Authorization Model\nImmutable Model Version"]
    end

    UI -->|"Create / edit model"| API
    UI -->|"Create / modify relationships"| API

    API -->|"Store / version model"| MODEL_REPO
    MODEL_REPO --> MODEL_VALIDATOR
    MODEL_VALIDATOR -->|"Publish model"| FGA_MODEL

    %% =========================
    %% DATA PLANE
    %% =========================

    subgraph FGA["OpenFGA Authorization Service"]
        OPENFGA["OpenFGA Server\nAuthorization Decision Engine"]
    end

    FGA_MODEL -->|"Active authorization model"| OPENFGA

    %% =========================
    %% DATASTORE
    %% =========================

    POSTGRES["PostgreSQL\nOpenFGA Datastore"]

    OPENFGA <-->|"Read / write\nmodels + tuples"| POSTGRES

    %% =========================
    %% APPLICATIONS
    %% =========================

    APP1["Application / Service A"]
    APP2["Application / Service B"]
    APPN["Application / Service N"]

    APP1 -->|"Check(user, relation, object)"| OPENFGA
    APP2 -->|"Check(user, relation, object)"| OPENFGA
    APPN -->|"Check(user, relation, object)"| OPENFGA

    OPENFGA -->|"allowed: true/false"| APP1
    OPENFGA -->|"allowed: true/false"| APP2
    OPENFGA -->|"allowed: true/false"| APPN

    %% =========================
    %% WRITE / RELATIONSHIP MANAGEMENT
    %% =========================

    API -->|"Write tuples"| OPENFGA
    OPENFGA -->|"Persist tuples"| POSTGRES

    %% =========================
    %% LIST / QUERY
    %% =========================

    APP1 -->|"ListObjects / BatchCheck"| OPENFGA
    OPENFGA -->|"Authorized objects / decisions"| APP1

    %% =========================
    %% CONTEXT
    %% =========================

    IDP["Identity Provider"]
    CONTEXT["Runtime Context\nLocation / Time / Zone / etc."]

    APP1 -.->|"Identity"| IDP
    APP2 -.->|"Identity"| IDP
    APPN -.->|"Identity"| IDP

    APP1 -.->|"Context / Contextual Tuples"| CONTEXT

    %% =========================
    %% AUDIT
    %% =========================

    AUDIT["Audit Event Pipeline"]
    AUDITSTORE["Audit Store / SIEM"]

    OPENFGA -.->|"Application-integrated\nauthorization telemetry"| AUDIT
    API -.->|"Model / tuple change audit"| AUDIT
    AUDIT --> AUDITSTORE

    classDef control fill:#e8f0fe,stroke:#4285f4,color:#111;
    classDef fga fill:#e8f5e9,stroke:#34a853,color:#111;
    classDef db fill:#fff3e0,stroke:#fb8c00,color:#111;
    classDef ext fill:#f3e5f5,stroke:#8e44ad,color:#111;

    class UI,API,MODEL_VALIDATOR control;
    class OPENFGA,FGA_MODEL fga;
    class POSTGRES,MODEL_REPO,AUDITSTORE db;
    class IDP,CONTEXT ext;
```

## openfga
```
Application
     ↓
OpenFGA
     ↓
Authorization datastore
     ↓
relationship evaluation
     ↓
decision
```

## Conceptual Evaluation Flow

                        AUTH REQUEST
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
        Subject           Resource           Context
           │                 │                 │
           ▼                 ▼                 ▼
      User / Role       Resource attrs     Location
      Department        Classification     Time
      Team              Department         Event Zone
      Clearance         Team              etc.
           │                 │                 │
           └─────────────────┼─────────────────┘
                             ▼
                      Rego Policy
                             │
                             ▼
                       OPA Evaluation
                             │
                             ▼
                    Structured Decision