# Notification Client service

This service receives analytics notifications via a _REST API_ and exposes metrics using _Prometheus_ (which is then
used by _Grafana_ to display the data). It tracks predicted throughput per _SUPI_ and updates a _Prometheus_ gauge
accordingly.

## Pre-requisites

* _Python_ ≥ 3.12 (preferably in a virtualenv, or using [Conda](https://anaconda.org/anaconda/conda))
* _FastAPI_
* _uvicorn_
* _httpx_
* _prometheus_fastapi_instrumentator_

## Configuration

The following environment variables configure the service:

* `NOTIF_CLIENT_SERVICE_PORT`: Port on which the service listens (e.g., 8080)
* `NOTIF_CLIENT_LOG_LEVEL`: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')

## API Endpoints

### Analytics Notification

> **POST** /analytics-notification

Handles analytics notifications containing throughput information.

**Example request body:**

```json
{
  "event_notifications": [
    {
      "predicted_throughput_infos": [
        {
          "supi": "imsi-208930000000001",
          "throughput": "15.5 Mbps"
        }
      ]
    }
  ]
}
```

## Prometheus Metrics

### Predicted Throughput Gauge

| Metric name            | Description                  | Labels |
|------------------------|------------------------------|--------|
| `predicted_throughput` | Predicted throughput in Mbps | `supi` |

Example metric output in _Prometheus_ format:

```
predicted_throughput{supi="imsi-208930000000001"} 15.5
```
