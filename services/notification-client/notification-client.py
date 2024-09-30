import logging
import os
import signal

import uvicorn
from fastapi import FastAPI
from nwdaf_api.models.nnwdaf_events_subscription_notification import NnwdafEventsSubscriptionNotification
from starlette import status

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()


@app.post("/analytics-notification", status_code=status.HTTP_204_NO_CONTENT)
async def analytic_notif(notif: NnwdafEventsSubscriptionNotification):
    logging.info(f"Received an analytics notification: {notif.model_dump_json(exclude_unset=True)}")
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

    try:
        uvicorn.run(app, host='0.0.0.0', port=8181, log_level='warning', loop='asyncio')
    except KeyboardInterrupt:
        logging.info("Application stopped")