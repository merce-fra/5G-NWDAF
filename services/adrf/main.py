# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

import logging
import os
import signal
import sys

from nwdaf_libcommon.AdrfService import AdrfService

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
        logging.info("Starting ADRF service...")

        service = AdrfService("adrf", kafka_bootstrap_server, mongo_uri, "adrf")
        service.run()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
