import asyncio
import logging
import os
import random
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

import httpx
import uvicorn
from fastapi import FastAPI, Response

from nwdaf_api.models import (
    RanEventSubscription,
    RanEventExposureNotification,
    RsrpInfo,
    RanEvent
)

from pydantic import BaseModel
from starlette import status

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

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


app = FastAPI(lifespan=lifespan)

service_name = "ran"
port = 10007
rsrp_subscriptions: dict[str, RanSubscriptionData] = dict()

BaseModel.Config = type('Config', (), {
    'json_encoders': {
        datetime: lambda v: v.isoformat()
    }
})


@app.post("/ran-event-exposure/v1/subscriptions")
async def ran_ee_subscription_handler(ran_sub: RanEventSubscription):
    logging.info(f"Received new RAN event exposure subscription: {ran_sub.model_dump_json(exclude_unset=True)}")
    subscription_id = str(uuid4())
    notification_interval = timedelta(seconds=ran_sub.periodicity)
    rsrp_subscriptions[subscription_id] = RanSubscriptionData(ran_sub=ran_sub,
                                                              next_notification_time=datetime.now() + notification_interval)

    return Response(status_code=status.HTTP_201_CREATED,
                    content=ran_sub.model_dump_json(exclude_unset=True),
                    media_type="application/json",
                    headers={
                        "Location": f"http://{service_name}:{port}/ran-event-exposure/v1/subscriptions/{subscription_id}"})


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
                notifications_to_send.append((subscription_id, subscription_data.ran_sub))

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
    for ue_id in ran_sub.ue_ids:
        logging.debug("Generating RSRP info notification with random data")

        # Generate random UE location data
        lte_rsrp = random.randint(-140, -44)
        nr_ssRsrp = random.uniform(-139.0, -68.0)

        notification = RanEventExposureNotification(event=RanEvent.RSRP_INFO,
                                                    timestamp=datetime.now(),
                                                    correlation_id=ran_sub.correlation_id,
                                                    rsrp_infos=[RsrpInfo(ue_id=ue_id,
                                                                         nr_ss_rsrp=nr_ssRsrp,
                                                                         lte_rsrp=lte_rsrp)])

        response = None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                logging.info(
                    f"Sending RSRP info notification to '{ran_sub.notif_uri}' for subscription id '{subscription_id}': {notification.model_dump_json(exclude_unset=True)}")
                response = await client.post(ran_sub.notif_uri,
                                             data=notification.model_dump_json(exclude_unset=True),
                                             timeout=5.0)
                response.raise_for_status()
                logging.info(
                    f"Sent notification to {ran_sub.notif_uri} (status code: {response.status_code})")

        except httpx.HTTPError as e:
            logging.error(f"Failed to send notification for subscription {subscription_id}: {str(e)}")
            if response is not None:
                logging.error(f"Response '{response.text}' (status code: {response.status_code})")
            else:
                logging.error("No response received.")


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=port, log_level='warning', loop='asyncio')
