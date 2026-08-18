## Hybrid OpenFGA + OPA runtime evaluation
```mermaid
flowchart LR

    APP["Application / Client"]

    REQUEST["Authorization Request
    subject + resource + action + context"]

    GATEWAY["Hybrid Authorization Gateway"]

    FGA["OpenFGA
    Relationship Evaluation"]

    MODEL["OpenFGA Model + Relationship Tuples"]

    RELATION["Relationship Decision
    ALLOW / DENY"]

    OPA["OPA
    Rego Policy Evaluation"]

    POLICY["Rego Policies
    + Attributes / Context"]

    FINAL["Final Decision
    ALLOW / DENY"]

    APP -->|"Authorization request"| REQUEST
    REQUEST --> GATEWAY

    GATEWAY -->|"Check relationship"| FGA
    MODEL --> FGA

    FGA -->|"Relationship result"| RELATION
    RELATION --> GATEWAY

    GATEWAY -->|"Relationship result
    + attributes + context"| OPA
    POLICY --> OPA

    OPA -->|"Policy result"| FINAL
    FINAL --> APP
```

## Runtime flow
```
Authorization Request
        ↓
Hybrid Gateway
        ↓
OpenFGA
        ↓
Relationship Decision
        ↓
OPA / Rego
        ↓
Attribute + Context Policy Evaluation
        ↓
Final ALLOW / DENY
```

## Decision composition 
```
OpenFGA = relationship authorization

OPA = attribute / contextual policy

Final:
    OpenFGA ALLOW
        AND
    OPA ALLOW
        ↓
      ALLOW
```
## Scenario
```
OpenFGA DENY → DENY

OpenFGA ALLOW + OPA DENY → DENY
```