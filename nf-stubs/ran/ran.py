import asyncio
import logging
import os
import random
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import httpx

logging.getLogger('httpx').setLevel(logging.WARNING)

import uvicorn

logging.getLogger("uvicorn").setLevel(logging.WARNING)

from fastapi import FastAPI, Response

from nwdaf_api.models import (
    RanEventSubscription,
    RanEventExposureNotification,
    RsrpInfo,
    RanEvent
)

from pydantic import BaseModel, ValidationError
from starlette import status

# Log level
log_level = os.getenv('RAN_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

# Service name
service_name = os.getenv('RAN_SERVICE_NAME')

# Service port
service_port = int(os.getenv('RAN_SERVICE_PORT'))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Start background task when app starts
    notification_task = asyncio.create_task(send_notifications())

    # Yield control to the application
    yield

    # Cancel the notification task when app shuts down
    notification_task.cancel()


@dataclass
class RanSubscriptionData:
    ran_sub: RanEventSubscription = None
    next_notification_time: datetime = None
    notification_count: int = 0


class RanData(BaseModel):
    lte_rsrp: Optional[int]
    nr_ssRsrp: Optional[float]


next_data: Optional[RanData] = None

app = FastAPI(lifespan=lifespan)

rsrp_subscriptions: dict[str, RanSubscriptionData] = dict()

BaseModel.Config = type('Config', (), {
    'json_encoders': {
        datetime: lambda v: v.isoformat()
    }
})


@app.post("/ran-event-exposure/v1/subscriptions")
async def ran_ee_subscription_handler(ran_sub: RanEventSubscription):
    logging.info(
        f"Received periodic RSRP info subscription for UE '{ran_sub.ue_ids[0]}': PERIODICITY={ran_sub.periodicity}s, "
        f"CORRELATION_ID='{ran_sub.correlation_id}'")
    subscription_id = str(uuid4())
    notification_interval = timedelta(seconds=ran_sub.periodicity)
    rsrp_subscriptions[subscription_id] = RanSubscriptionData(ran_sub=ran_sub,
                                                              next_notification_time=datetime.now() + notification_interval)

    return Response(status_code=status.HTTP_201_CREATED,
                    content=ran_sub.model_dump_json(exclude_unset=True),
                    media_type="application/json",
                    headers={
                        "Location": f"http://{service_name}:{service_port}/ran-event-exposure/v1/subscriptions/{subscription_id}"})


@app.post("/data")
async def receive_data(ran_data: RanData):
    global next_data
    logging.debug(f"Received data: {ran_data.model_dump_json(exclude_unset=True)}")
    next_data = ran_data
    return {"message": "Data received successfully", "received_data": ran_data.model_dump_json(exclude_unset=True)}


def should_notify(subscription_data: RanSubscriptionData):
    is_time_to_notify = (
            subscription_data.next_notification_time is None or subscription_data.next_notification_time <= datetime.now())

    return is_time_to_notify


async def send_notifications():
    while True:
        # Create a list to store notifications that need to be sent in this cycle
        notifications_to_send = []

        for subscription_id, subscription_data in rsrp_subscriptions.items():
            if should_notify(subscription_data):
                logging.debug("A new notification is ready to be sent")
                notifications_to_send.append((subscription_data.ran_sub.correlation_id, subscription_data.ran_sub))

                notification_interval = timedelta(seconds=subscription_data.ran_sub.periodicity)
                subscription_data.next_notification_time += notification_interval
                subscription_data.notification_count += 1

        # Send notifications concurrently
        if notifications_to_send:
            await asyncio.gather(
                *[notify(subscription_id, input_data) for subscription_id, input_data in notifications_to_send]
            )

        await asyncio.sleep(0.3)


async def notify(subscription_id: str, ran_sub: RanEventSubscription):
    global next_data
    for ue_id in ran_sub.ue_ids:
        logging.debug("Generating RSRP info notification with random data")

        lte_rsrp = random.randint(-140, -44) if next_data is None or next_data.lte_rsrp is None else next_data.lte_rsrp
        nr_ssRsrp = random.uniform(-139.0,
                                   -68.0) if next_data is None or next_data.nr_ssRsrp is None else next_data.nr_ssRsrp

        notification = None
        try:
            notification = RanEventExposureNotification(event=RanEvent.RSRP_INFO,
                                                        time_stamp=datetime.now(),
                                                        correlation_id=subscription_id,
                                                        rsrp_infos=[RsrpInfo(ue_id=ue_id,
                                                                             nr_ss_rsrp=nr_ssRsrp,
                                                                             lte_rsrp=lte_rsrp)])
            logging.debug(
                f"Crafted RAN event exposure notification: {notification.model_dump_json(exclude_unset=True)}")
        except ValidationError as err:
            error_messages = "\n".join([f"{e['loc']}: {e['msg']}" for e in err.errors()])
            logging.error(f"Validation error creating RanEventExposureNotification: {error_messages}")

        response = None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                logging.info(f"Sending RSRP information for UE '{ue_id}'...")
                logging.debug(
                    f"Sending RSRP info notification to '{ran_sub.notif_uri}' for subscription id '{subscription_id}': {notification.model_dump_json(exclude_unset=True)}")
                response = await client.post(ran_sub.notif_uri,
                                             data=notification.model_dump_json(exclude_unset=True),
                                             timeout=5.0)
                response.raise_for_status()
                logging.debug(
                    f"Sent notification to {ran_sub.notif_uri} (status code: {response.status_code})")

        except httpx.HTTPError as e:
            logging.error(f"Failed to send notification for subscription {subscription_id}: {str(e)}")
            if response is not None:
                logging.error(f"Response '{response.text}' (status code: {response.status_code})")
            else:
                logging.error("No response received.")


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=service_port, log_level='warning', loop='asyncio')
