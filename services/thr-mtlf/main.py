import logging
import os
import signal
import sys

from ThroughputMtlfService import ThroughputMtlfService

# Log level
log_level = os.getenv('THR_MTLF_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka boostrap server
kafka_bootstrap_server = os.getenv('KAFKA_BOOTSTRAP_SERVER')

# Service name
service_name = os.getenv('THR_MTLF_SERVICE_NAME')

service = ThroughputMtlfService(service_name, kafka_bootstrap_server)


def handle_signal(sig, _frame):
    if sig == signal.SIGINT:
        logging.info("Received SIGINT (Ctrl-C), shutting down gracefully...")
    elif sig == signal.SIGTERM:
        logging.info("Received SIGTERM, shutting down gracefully...")

    service.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

if __name__ == '__main__':
    try:
        service.run()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
