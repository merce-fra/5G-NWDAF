import logging
import os
import signal

import uvicorn
from fastapi import FastAPI
from nwdaf_api.models.nnwdaf_events_subscription_notification import NnwdafEventsSubscriptionNotification
from starlette import status
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

instrumentator = Instrumentator()

# Prometheus gauge for throughput
predicted_throughput_gauge = Gauge(
    'predicted_throughput',
    'Predicted throughput in Kbps',
    ['supi']
)

@app.post("/analytics-notification", status_code=status.HTTP_204_NO_CONTENT)
async def analytic_notif(notif: NnwdafEventsSubscriptionNotification):
    logging.info(f"Received an analytics notification: {notif.model_dump_json(exclude_unset=True)}")

    # Update the Prometheus gauge
    for event in notif.event_notifications:
        if event.predicted_throughput_infos is not None:
            for info in event.predicted_throughput_infos:
                supi = info.supi
                throughput_value = float(info.throughput.replace(" Kbps", "").strip())
                predicted_throughput_gauge.labels(supi=supi).set(throughput_value)
                logging.info(f"Updated predicted throughput for {supi}: {throughput_value} Kbps")

    return


# Handle signals for graceful shutdown
def handle_shutdown_signal(signal_name):
    logging.info(f"Received {signal_name}. Shutting down gracefully...")
    # Perform cleanup tasks here if necessary
    raise KeyboardInterrupt  # Raise exception to stop the app


def register_signal_handlers():
    signal.signal(signal.SIGINT, lambda signum, frame: handle_shutdown_signal("SIGINT"))
    signal.signal(signal.SIGTERM, lambda signum, frame: handle_shutdown_signal("SIGTERM"))


if __name__ == '__main__':
    register_signal_handlers()
    instrumentator.instrument(app).expose(app)

    try:
        uvicorn.run(app, host='0.0.0.0', port=8181, log_level='warning', loop='asyncio')
    except KeyboardInterrupt:
        logging.info("Application stopped")