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
from fastapi import FastAPI
from nwdaf_api.models.event_notify_data_ext import EventNotifyDataExt
from nwdaf_api.models.event_notify_data_type import EventNotifyDataType
from nwdaf_api.models.geographical_coordinates import GeographicalCoordinates
from nwdaf_api.models.velocity_estimate import VelocityEstimate
from nwdaf_api.models.horizontal_velocity import HorizontalVelocity
from nwdaf_api.models.input_data import InputData
from nwdaf_api.models.geographic_area import GeographicArea
from nwdaf_api.models.point import Point
from nwdaf_api.models.supported_gad_shapes import SupportedGADShapes
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
class GmlcSubscriptionData:
    input_data: InputData = None
    next_notification_time: datetime = None
    notification_count: int = 0


app = FastAPI(lifespan=lifespan)

service_name = "gmlc"
port = 10006
location_subscriptions: dict[str, GmlcSubscriptionData] = dict()

BaseModel.Config = type('Config', (), {
    'json_encoders': {
        datetime: lambda v: v.isoformat()
    }
})


@app.post("/ngmlc-loc/v1/provide-location", status_code=status.HTTP_200_OK)
async def provide_location_sub(input_data: InputData):
    logging.info(f"Received new GMLC input data: {input_data.model_dump_json(exclude_unset=True)}")
    subscription_id = str(uuid4())
    notification_interval = timedelta(
        seconds=input_data.periodic_event_info.reporting_interval
    )
    location_subscriptions[subscription_id] = GmlcSubscriptionData(input_data=input_data,
                                                                   next_notification_time=datetime.now()+notification_interval)

    return


def should_notify(subscription_data: GmlcSubscriptionData):
    is_time_to_notify = (
            subscription_data.next_notification_time is None or subscription_data.next_notification_time <= datetime.now())

    is_amount_ok = (
            subscription_data.input_data.periodic_event_info.reporting_infinite_ind or subscription_data.notification_count <= subscription_data.input_data.periodic_event_info.reporting_amount)

    return is_time_to_notify and is_amount_ok


async def send_notifications():
    while True:
        # Create a list to store notifications that need to be sent in this cycle
        notifications_to_send = []

        for subscription_id, subscription_data in location_subscriptions.items():
            if should_notify(subscription_data):
                logging.debug("A new notification is ready to be sent")
                notifications_to_send.append((subscription_id, subscription_data.input_data))

                notification_interval = timedelta(
                    seconds=subscription_data.input_data.periodic_event_info.reporting_interval
                )

                subscription_data.next_notification_time += notification_interval
                subscription_data.notification_count += 1

        # Send notifications concurrently
        if notifications_to_send:
            await asyncio.gather(
                *[notify(subscription_id, input_data) for subscription_id, input_data in notifications_to_send]
            )

        await asyncio.sleep(0.3)


async def notify(subscription_id: str, input_data: InputData):
    logging.debug("Generating GMLC location notification with random data")
    # Generate random UE location data
    latitude = random.uniform(44.9732550, 44.97696380)
    longitude = random.uniform(-93.25899079999999, -93.26375390000001)
    coordinates = GeographicalCoordinates(lon=longitude, lat=latitude)
    point = Point(shape=SupportedGADShapes.POINT, point=coordinates)
    location_estimate = GeographicArea(anyof_schema_1_validator=point)

    # Generate random UE velocity data
    speed = random.uniform(0.00010015551, 9.9988235)
    compass_direction = random.randint(0, 360)
    horizontal_velocity = HorizontalVelocity(h_speed=speed, bearing=compass_direction)
    velocity_estimate = VelocityEstimate(anyof_schema_1_validator=horizontal_velocity)

    notification = EventNotifyDataExt(ldr_reference=input_data.ldr_reference,
                                      event_notify_data_type=EventNotifyDataType.PERIODIC,
                                      supi=input_data.supi,
                                      timestamp_of_location_estimate=datetime.now(),
                                      location_estimate=location_estimate,
                                      velocity_estimate=velocity_estimate)

    response = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            logging.info(
                f"Sending location notification to '{input_data.hgmlc_call_back_uri}' for subscription id '{subscription_id}': {notification.model_dump_json(exclude_unset=True)}")
            response = await client.post(input_data.hgmlc_call_back_uri,
                                         data=notification.model_dump_json(exclude_unset=True),
                                         timeout=5.0)
            response.raise_for_status()
            logging.info(
                f"Sent notification to {input_data.hgmlc_call_back_uri} (status code: {response.status_code})")

    except httpx.HTTPError as e:
        logging.error(f"Failed to send notification for subscription {subscription_id}: {str(e)}")
        if response is not None:
            logging.error(f"Response '{response.text}' (status code: {response.status_code})")
        else:
            logging.error("No response received.")


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=port, log_level='warning', loop='asyncio')
