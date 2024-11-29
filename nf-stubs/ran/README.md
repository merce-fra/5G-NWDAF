# _RAN_ stub service

This is a _RAN_ stub service using _FastAPI_ which can provide _RSRP_ (_Reference Signal Received Power_) information.

It accepts subscriptions, and can send event exposure notifications to its subscribers. It either generates random
_RSRP_
data within a given range, or receives this data from an external source (typically, the
_[CSV File Player](../csv_file_player)_ service)

> **NB**: The _RAN Event Exposure_ service doesn't exist in the _3GPP_ specifications. This service has been implemented
> in order to fit our use case, but would not exist in an actual _5G_ core network.

## Pre-requisites

* _Python_ ≥ 3.12 (preferably in a virtualenv, or using [Conda](https://anaconda.org/anaconda/conda))
* _FastAPI_
* _uvicorn_
* _httpx_

## Configuration

The following environment variables are needed to configure the service:

* `RAN_SERVICE_NAME`: The name of the service, typically '_ran_'
* `RAN_SERVICE_PORT`: The port used by the service, typically '_10007_'
* `RAN_LOG_LEVEL`; The logging level of the service ('_DEBUG_', '_INFO_', '_WARNING_', etc.)

## API Endpoints

This service exposes two _HTTP_ endpoints

### RSRP Event Subscription

> **POST** _/ran-event-exposure/v1/subscriptions_

**Example request body**:

```json
{
  "ue_ids": [
    "ue-123"
  ],
  "periodicity": 5,
  "correlation_id": "corr-id-001",
  "notif_uri": "http://example.com/notify"
}
```

This request will create a subscription that will send a notification every 5 seconds to _http://example.com/notify_,
containing _RSRP_ information for _UE_ `ue-123`

### Receive RSRP data

> **POST** _/data_

This endpoint will be used by another service (typically, the _CSV File Player_) to send RSRP data coming from an
external source (e.g. a _CSV_ file).

**Example request body**:
```json
{
  "lte_rsrp": -90,
  "nr_ssRsrp": -110.5
}
```