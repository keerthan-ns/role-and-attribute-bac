## Architecture diagram
```
Test / benchmark client
        │
        ▼
   OPA HTTP API
        │
        ▼
  Rego policy evaluation
        │
        ├── policy files
        ├── request input
        └── optional policy data
```

## OPA + Rego runtime evaluation
```mermaid
flowchart LR

    APP["Application / Client"]

    REQUEST["Authorization Request
    subject + resource + action + context"]

    OPA["OPA
    Policy Engine"]

    REGO["Rego Policies"]

    DATA["Policy / Attribute Data"]

    DECISION["ALLOW / DENY
    Structured Decision"]

    APP -->|Authorization request| REQUEST
    REQUEST --> OPA

    REGO --> OPA
    DATA --> OPA

    OPA -->|Evaluate policy| DECISION
    DECISION --> APP
```

## Runtime flow
```
Request
   ↓
OPA
   ├── Rego Policy
   ├── Policy / Attribute Data
   └── Request Input
          ↓
      Policy evaluation
          ↓
      ALLOW / DENY
```

----------------------------------------------------
# Additional (runtime specific - full flow)
----------------------------------------------------

## Current runtime architecture
```mermaid
flowchart LR

    CLIENT["POC Test / Benchmark Client"]

    subgraph LOCAL["POC-A Local Environment"]
        OPA["OPA Server\nlocalhost:8181"]

        POLICIES["Rego Policies\n*.rego"]

        DATA["Policy / Attribute Data\nJSON / bundled data"]

        OPA -->|"loads"| POLICIES
        OPA -->|"loads / evaluates"| DATA
    end

    DATASET["Shared POC Dataset\nUsers / Resources / Attributes"]

    CLIENT -->|"POST /v1/data/.../decision\nAuthorization input"| OPA
    DATASET -->|"request/test data"| CLIENT

    OPA -->|"ALLOW / DENY /\nstructured result"| CLIENT
```

### Actual request path
```
Benchmark / test client
        ↓
OPA
        ↓
Rego
        ↓
decision
```