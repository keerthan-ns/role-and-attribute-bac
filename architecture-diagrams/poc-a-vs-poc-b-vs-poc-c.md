## POC A - OPA + Rego
```mermaid
flowchart LR
    A["Authorization Request"] --> B["OPA"]
    C["Rego Policies + Data"] --> B
    B --> D["ALLOW / DENY"]
```

## POC-B Phase 1 — OpenFGA
```mermaid
flowchart LR
    A["Authorization Request"] --> B["OpenFGA"]
    C["Authorization Model + Tuples"] --> B
    B --> D["ALLOW / DENY"]
```

## POC-B Phase 2 — OpenFGA
```mermaid
flowchart LR
    A["Authorization Request"] --> B["OpenFGA"]
    C["Authorization Model + Tuples"] --> B
    E["Conditions / Contextual Tuples"] --> B
    B --> D["ALLOW / DENY"]
```

## POC-B Phase 1 — OpenFGA
```mermaid
flowchart LR
    A["Authorization Request"] --> B["Hybrid Gateway"]

    C["OpenFGA Model + Tuples"] --> D["OpenFGA"]
    B -->|"Relationship Check"| D
    D -->|"Relationship Decision"| B

    B -->|"Relationship + Attributes + Context"| E["OPA / Rego"]
    F["Rego Policies"] --> E

    E --> G["Final ALLOW / DENY"]
```

## Additional
```
OPA
 │
 └── Policy evaluation

OpenFGA
 │
 └── Relationship evaluation

OpenFGA Phase 2
 │
 ├── Relationship evaluation
 └── Conditions / Context

Hybrid
 │
 ├── OpenFGA → Relationship
 └── OPA     → Policy / Attributes / Context
```