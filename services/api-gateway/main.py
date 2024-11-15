import logging
import os
import signal
import sys

from nwdaf_api.models.nf_type import NFType
from nwdaf_libcommon.ApiGatewayService import ApiGatewayService

# Log level
log_level = os.getenv('API_GW_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka bootstrap server
kafka_bootstrap_server = os.getenv('KAFKA_BOOTSTRAP_SERVER')

# Service name & port
service_name = os.getenv('API_GW_SERVICE_NAME')
service_port = int(os.getenv('API_GW_SERVICE_PORT'))

# Initialize service and NF registry from env variables
service = ApiGatewayService(service_name, service_port, kafka_bootstrap_server, {NFType.GMLC, NFType.RAN})
service.init_nf_registry([(NFType.GMLC, os.getenv('GMLC_SERVICE_NAME'), int(os.getenv('GMLC_SERVICE_PORT'))),
                          (NFType.RAN, os.getenv('RAN_SERVICE_NAME'), int(os.getenv('RAN_SERVICE_PORT')))])


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
