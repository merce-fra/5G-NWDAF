import asyncio
import logging
import random
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from uuid import uuid4

from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, Response
from nwdaf_api.models.nsmf_event_exposure import NsmfEventExposure
from nwdaf_api.models.nsmf_event_exposure_notification import NsmfEventExposureNotification
from nwdaf_api.models.smf_event_notification import SmfEventNotification
from starlette import status


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Start background task when app starts
    notification_task = asyncio.create_task(send_notifications())

    # Yield control to the application
    yield

    # Cancel the notification task when app shuts down
    notification_task.cancel()


app = FastAPI(lifespan=lifespan)

service_name = "gmlc"
port = 10001
subscriptions: dict[str, NsmfEventExposure] = dict()

BaseModel.Config = type('Config', (), {
    'json_encoders': {
        datetime: lambda v: v.isoformat()
    }
})


@app.post("/nsmf-event-exposure/v1/subscriptions")
async def ee_sub(subscription: NsmfEventExposure):
    logging.info(f"Received an analytics notification: {subscription.model_dump_json(exclude_unset=True)}")

    subscription_id = str(uuid4())
    subscriptions[subscription_id] = subscription

    return Response(status_code=status.HTTP_201_CREATED,
                    content=subscription.model_dump_json(exclude_unset=True),
                    media_type="application/json",
                    headers={
                        "Location": f"http://{service_name}:{port}/nsmf-event-exposure/v1/subscriptions/{subscription_id}"})


async def send_notifications():
    async with httpx.AsyncClient() as client:
        while True:
            if subscriptions:
                for sub_id, subscription in subscriptions.items():
                    endpoint = subscription.notif_uri
                    notification_data = NsmfEventExposureNotification(
                        notif_id=sub_id,
                        event_notifs=[SmfEventNotification(
                            event=subscription.event_subs[0].event,
                            time_stamp=datetime.now()
                        )]
                    )

                    # Log the notification data being sent
                    logging.info(
                        f"Sending notification payload: {notification_data.model_dump(exclude_unset=True)}")

                    try:
                        # Send the request
                        response = await client.post(endpoint,
                                                     data=notification_data.model_dump_json(exclude_unset=True))

                        if response.status_code == 422:
                            # Log validation error details from the response
                            logging.error(f"422 Unprocessable Entity: {response.text}")
                        else:
                            logging.info(f"Sent notification to {endpoint}, status: {response.status_code}")

                    except Exception as e:
                        logging.error(f"Failed to send notification to {endpoint}: {e}")

            await asyncio.sleep(random.randint(5, 20))


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    uvicorn.run(app, host='0.0.0.0', port=port, log_level='warning', loop='asyncio')
