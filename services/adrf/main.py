import logging
import os
import signal
import sys

from pymongo import MongoClient

# Log level
log_level = os.getenv('ADRF_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka boostrap server
kafka_bootstrap_server = os.getenv('KAFKA_BOOTSTRAP_SERVER')

# Service name
service_name = os.getenv('ADRF_SERVICE_NAME')

# Mongo URI
mongo_uri = os.getenv('MONGO_URI')


def handle_signal(sig, _frame):
    if sig == signal.SIGINT:
        logging.info("Received SIGINT (Ctrl-C), shutting down gracefully...")
    elif sig == signal.SIGTERM:
        logging.info("Received SIGTERM, shutting down gracefully...")

    # service.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

if __name__ == '__main__':
    try:
        logging.info("ADRF POC")

        client = MongoClient(mongo_uri)
        db = client['adrf']
        collection = db["example_collection"]

        # Insert multiple documents
        documents = [
            {"name": "Bob", "age": 30, "city": "London"},
            {"name": "Charlie", "age": 35, "city": "New York"},
            {"name": "John", "age": 22, "city": "London"}
        ]

        insert_many_result = collection.insert_many(documents)
        logging.info(f"Inserted documents with IDs: {insert_many_result.inserted_ids}")

        logging.info("Find all documents:")
        for doc in collection.find({"city": "London"}):
            logging.info(doc)

        collection.drop()

        client.close()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
