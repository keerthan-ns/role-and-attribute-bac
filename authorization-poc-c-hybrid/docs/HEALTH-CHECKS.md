# POC-C Health Checks

OpenFGA and OPA use minimal images that do not include `wget`, so Docker
container healthchecks are not used for these two services.

Service readiness is checked by `scripts/bootstrap.ps1` from the host:

```text
OpenFGA  http://localhost:8091/healthz
OPA      http://localhost:8182/health
Gateway  http://localhost:8090/health
```

OpenFGA `/healthz` reports datastore-backed service status.
OPA `/health` reports operational health/readiness.
