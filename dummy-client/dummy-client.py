import logging

import uvicorn
from fastapi import FastAPI, Request

from starlette import status

app = FastAPI()


@app.post("/analytics-notification", status_code=status.HTTP_204_NO_CONTENT)
async def analytic_notif(request: Request):
    json_data = await request.json()
    logging.info(f"Received an analytics notification: {json_data}")
    return


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    uvicorn.run(app, host='0.0.0.0', port=8181, log_level='warning', loop='asyncio')
