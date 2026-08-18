# POC-C Isolation

POC-C has its own containers, network, PostgreSQL volume and host ports:

- `pocc-postgres`
- `pocc-openfga`
- `pocc-opa`
- `pocc-gateway`
- network: `authorization-poc-c-network`
- volume: `authorization-poc-c-postgres-data`
- OpenFGA HTTP: `8091`
- OPA HTTP: `8182`
- Gateway HTTP: `8090`
- PostgreSQL: `5440`

POC-C does not connect to the POC-B OpenFGA or PostgreSQL resources.
