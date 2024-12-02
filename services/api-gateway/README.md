# API Gateway service

This is an _API Gateway_ service written in _Python_, that fits within a _Kafka_-based _NWDAF_
microservices architecture.

## Pre-requisites

To build this project, these pre-requisites are needed:

* _Python_ ≥ 3.12 (preferably in a _virtualenv_, or using [Conda](https://anaconda.org/anaconda/conda))
* _FastAPI_
* _confluent-kafka_
* _aiohttp_
* _uvicorn_
* _httpx_

## Configuration

The following environment variables configure the service:

* `API_GW_LOG_LEVEL`: Logging level ('DEBUG', 'INFO', etc.)
* `KAFKA_BOOTSTRAP_SERVER`: _Kafka_ bootstrap server address
* `API_GW_SERVICE_NAME`: Name of the _API Gateway_ service
* `API_GW_SERVICE_PORT`: Port on which the service listens
* `GMLC_SERVICE_NAME`: _GMLC_ service name for _NF_ registration
* `GMLC_SERVICE_PORT`: Port for the _GMLC_ service
* `RAN_SERVICE_NAME`: _RAN_ service name for _NF_ registration
* `RAN_SERVICE_PORT`: Port for the _RAN_ service



