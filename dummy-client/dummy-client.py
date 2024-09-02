import logging

import uvicorn
from fastapi import FastAPI
from nwdaf_api.models.nnwdaf_events_subscription_notification import NnwdafEventsSubscriptionNotification
from starlette import status

app = FastAPI()


@app.post("/analytics-notification", status_code=status.HTTP_204_NO_CONTENT)
async def analytic_notif(notif: NnwdafEventsSubscriptionNotification) :
    logging.info(f"Received an analytics notification: {notif.model_dump_json(exclude_unset=True)}")
    return


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    uvicorn.run(app, host='0.0.0.0', port=8181, log_level='warning', loop='asyncio')