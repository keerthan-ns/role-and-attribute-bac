## Runtime/Deployment Architecture
```mermaid
flowchart TB
    %% =========================
    %% CONTROL PLANE
    %% =========================

    subgraph CONTROL["Authorization Control Plane"]
        UI["React + ShadCN\nPolicy Administration UI"]

        API["Policy Management API\n(Create / Validate / Version / Publish)"]

        POLICY_REPO["Policy Repository\nGit / Policy Store"]

        POLICY_CI["Policy Validation & Test Pipeline\nRego Tests / Lint / Validation"]

        BUNDLE["Policy Bundle / Distribution\nOPA Bundle Server"]
    end

    UI -->|"Create / Edit policy"| API
    API -->|"Store versioned Rego"| POLICY_REPO

    POLICY_REPO -->|"Pull policies"| POLICY_CI
    POLICY_CI -->|"Validated policy"| BUNDLE

    %% =========================
    %% DATA PLANE
    %% =========================

    subgraph DATAPLANE["Authorization Data Plane"]
        OPA1["OPA Instance 1\nRego Policy Evaluation"]
        OPA2["OPA Instance 2\nRego Policy Evaluation"]
        OPAN["OPA Instance N\nRego Policy Evaluation"]

        APP1["Application / Service A\nPolicy Enforcement Point"]
        APP2["Application / Service B\nPolicy Enforcement Point"]
        APPN["Application / Service N\nPolicy Enforcement Point"]
    end

    BUNDLE -->|"Policy + static data\nbundle distribution"| OPA1
    BUNDLE -->|"Policy + static data\nbundle distribution"| OPA2
    BUNDLE -->|"Policy + static data\nbundle distribution"| OPAN

    APP1 -->|"Authorization request\nSubject + Resource + Action + Context"| OPA1
    APP2 -->|"Authorization request\nSubject + Resource + Action + Context"| OPA2
    APPN -->|"Authorization request\nSubject + Resource + Action + Context"| OPAN

    OPA1 -->|"ALLOW / DENY /\nstructured decision"| APP1
    OPA2 -->|"ALLOW / DENY /\nstructured decision"| APP2
    OPAN -->|"ALLOW / DENY /\nstructured decision"| APPN

    %% =========================
    %% IDENTITY / ATTRIBUTE DATA
    %% =========================

    IDP["Identity Provider\nOIDC / OAuth2 / LDAP / AD"]

    ATTRIBUTE_STORE["Identity / Attribute Source\nUsers / Departments / Teams /\nClearance / Location / etc."]

    APP1 -.->|"Authenticated identity / claims"| IDP
    APP2 -.->|"Authenticated identity / claims"| IDP
    APPN -.->|"Authenticated identity / claims"| IDP

    ATTRIBUTE_STORE -.->|"Relevant attributes\nwhen required"| APP1
    ATTRIBUTE_STORE -.->|"Relevant attributes\nwhen required"| APP2
    ATTRIBUTE_STORE -.->|"Relevant attributes\nwhen required"| APPN

    %% =========================
    %% AUDIT
    %% =========================

    AUDIT["Audit / Decision Log Pipeline"]

    OPA1 -->|"Decision log"| AUDIT
    OPA2 -->|"Decision log"| AUDIT
    OPAN -->|"Decision log"| AUDIT

    AUDIT --> AUDITSTORE["Long-term Audit Store / SIEM"]

    %% =========================
    %% ADMIN AUDIT
    %% =========================

    API -->|"Policy change audit"| AUDIT

    %% =========================
    %% STYLING
    %% =========================

    classDef control fill:#e8f0fe,stroke:#4285f4,color:#111;
    classDef data fill:#e8f5e9,stroke:#34a853,color:#111;
    classDef storage fill:#fff3e0,stroke:#fb8c00,color:#111;
    classDef external fill:#f3e5f5,stroke:#8e44ad,color:#111;

    class UI,API,POLICY_CI,BUNDLE control;
    class OPA1,OPA2,OPAN,APP1,APP2,APPN data;
    class POLICY_REPO,AUDITSTORE,ATTRIBUTE_STORE storage;
    class IDP external;
```

## Runtime flow
```
Application
    ↓
OPA
    ↓
ALLOW / DENY
    ↓
Application
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