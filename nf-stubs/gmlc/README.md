# _GMLC_ stub service

This is a _GMLC_ stub service using _FastAPI_ which can provide _UE_ location data.

It accepts subscriptions, and can send event exposure notifications to its subscribers. It either generates random location
data within a given range, or receives this data from an external source (typically, the
_[CSV File Player](../csv_file_player)_ service)


## Pre-requisites

* _Python_ ≥ 3.12 (preferably in a virtualenv, or using [Conda](https://anaconda.org/anaconda/conda))
* _FastAPI_
* _uvicorn_
* _httpx_

## Configuration

The following environment variables are needed to configure the service:

* `GMLC_SERVICE_NAME`: The name of the service, typically '_gmlc_'
* `GMLC_SERVICE_PORT`: The port used by the service, typically '_10006_'
* `GMLC_LOG_LEVEL`; The logging level of the service ('_DEBUG_', '_INFO_', '_WARNING_', etc.)

## API Endpoints

This service exposes two _HTTP_ endpoints

### Provide Location Subscription

> **POST** _/ngmlc-loc/v1/provide-location_

**Example request body**:

```json
{
  "supi": "imsi-208930000000001",
  "periodic_event_info": {
    "reporting_interval": 5,
    "reporting_amount": 10,
    "reporting_infinite_ind": false
  },
  "ldr_reference": "ldr-12345",
  "hgmlc_call_back_uri": "http://example.com/callback"
}
```

This request will create a subscription that will send a notification every 5 seconds to _http://example.com/callback_,
containing location information for _UE_ `imsi-208930000000001`

### Receive location data

> **POST** _/data_

This endpoint will be used by another service (typically, the _CSV File Player_) to send location data coming from an
external source (e.g. a _CSV_ file).

**Example request body**:
```json
{
  "latitude": 44.974,
  "longitude": -93.259,
  "movingSpeed": 3.5,
  "compassDirection": 45
}
```