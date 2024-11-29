# CSV File Player service

This service reads a _CSV_ file containing _UE_ data and sends it periodically to multiple endpoints (e.g., _GMLC_,
_RAN_) using _FastAPI_. It supports asynchronous background tasks for efficient data streaming.

## Pre-requisites

* _Python_ ≥ 3.12 (preferably in a virtualenv, or using [Conda](https://anaconda.org/anaconda/conda))
* _FastAPI_
* _uvicorn_
* _httpx_

## Configuration

The following environment variables configure the service:

* `CSV_FP_SERVICE_PORT`: Port on which the service runs (default example: 8000)
* `GMLC_SERVICE_NAME`: Hostname or IP for the GMLC service
* `GMLC_SERVICE_PORT`: Port for the GMLC service
* `RAN_SERVICE_NAME`: Hostname or IP for the RAN service
* `RAN_SERVICE_PORT`: Port for the RAN service
* `CSV_FP_LOG_LEVEL`: Logging level (e.g., DEBUG, INFO, WARNING, ERROR)

## How does it work?

* CSV Reading: Reads rows from a [_CSV_ file](./csv/Lumos5G-v1.0.csv) and converts fields to appropriate types.
* Data Sending: Sends the data to the _GMLC_ and RAN services asynchronously.
* Error Handling: Logs errors for _HTTP_ status and request issues.

## API Endpoint

### Start Sending CSV Data

> **GET** /start

Starts sending data from a CSV file at a periodic interval to the configured endpoints. This request doesn't need to
have a body.

**Example response:**

```json
{
  "message": "Started sending CSV data"
}
```

