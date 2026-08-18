# POC-C Scripts

## bootstrap.ps1

Canonical local setup sequence:

1. Wait for OpenFGA and OPA.
2. Create the OpenFGA store.
3. Create the Phase-1-aligned authorization model.
4. Write `FGA_STORE_ID` and `FGA_MODEL_ID` to `.env`.
5. Load `data/tuples.jsonl`.
6. Recreate the gateway with the generated IDs.
7. Verify the gateway health endpoint.

Run from the project root:

```powershell
.\scripts\bootstrap.ps1
```

Optional:

```powershell
.\scripts\bootstrap.ps1 -BatchSize 100
```

## OPA policy validation

The OPA image starts in server mode and loads `opa/policies` during startup.
The policy files therefore must parse successfully before `pocc-opa` can become
healthy.

The policy uses a constant default decision and evaluates request-dependent
fields only in the non-default decision rules.
