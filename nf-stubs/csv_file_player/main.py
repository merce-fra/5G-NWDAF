import logging
import os

import csv
import asyncio
import httpx

logging.getLogger('httpx').setLevel(logging.WARNING)

import uvicorn
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

# Log level
log_level = os.getenv('CSv_FP_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

# List of endpoints to send data
gmlc_service_name = os.getenv('GMLC_SERVICE_NAME')
gmlc_service_port = int(os.getenv('GMLC_SERVICE_PORT'))
ran_service_name = os.getenv('RAN_SERVICE_NAME')
ran_service_port = int(os.getenv('RAN_SERVICE_PORT'))
endpoints = [
    f"http://{gmlc_service_name}:{gmlc_service_port}/data",
    f"http://{ran_service_name}:{ran_service_port}/data"
]

# CSV file player service port
service_port = int(os.getenv('CSV_FP_SERVICE_PORT'))

FIELDS_CONVERSION = {
    "latitude": float,
    "longitude": float,
    "movingSpeed": float,
    "compassDirection": int,
    "lte_rsrp": int,
    "nr_ssRsrp": float
}


def convert_field_types(row):
    for field, field_type in FIELDS_CONVERSION.items():
        if field in row:
            # If the field is empty, set it to None
            if row[field] == '' or row[field] is None:
                row[field] = None
            else:
                # Try converting to the appropriate type, log a warning if it fails
                try:
                    row[field] = field_type(row[field])
                except ValueError as e:
                    logging.warning(f"Failed to convert {field} to {field_type.__name__}: {e}")
                    row[field] = None  # If conversion fails, set to None
        else:
            # If the field is missing in the row, set it to None
            row[field] = None
    return row


# Function to read CSV file and yield rows as dictionaries
async def read_csv(file_path):
    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row = convert_field_types(row)
            yield row


# Function to send data to multiple endpoints
async def send_data_to_endpoints(data):
    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            try:
                # Send the data and log success
                _response = await client.post(endpoint, json=data)

            except httpx.HTTPStatusError as e:
                # Log the status code, response details, and the request body in case of a 4xx/5xx error
                logging.error(f"HTTP error {e.response.status_code} from {endpoint}: {e.response.text}")
                logging.error(f"Response body: {e.response.text}")  # Log response body (e.g., validation errors)
                logging.error(f"Request body that caused error: {data}")

            except httpx.RequestError as e:
                # Log the request error and the request body in case of network-related issues
                logging.error(f"Request error while sending to {endpoint}: {e}")
                logging.error(f"Request body that caused error: {data}")


# Background task to send CSV data periodically
async def send_csv_periodically(file_path, interval=5):
    async for row in read_csv(file_path):
        logging.debug(f"Sending row: {row}")
        await send_data_to_endpoints(row)
        await asyncio.sleep(interval)


# FastAPI route to start sending CSV data periodically
@app.get("/start")
async def start_sending_data(background_tasks: BackgroundTasks):
    file_path = "csv/Lumos5G-v1.0.csv"
    interval = 5  # Seconds between sending each row
    background_tasks.add_task(send_csv_periodically, file_path, interval)
    logging.info(f"Starting to send CSV data from '{file_path}'...")
    return {"message": "Started sending CSV data"}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=service_port, log_level='warning', loop='asyncio')
