# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

import os
import sys
import time
import signal
from enum import Enum
from typing import Type
import logging

from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from nwdaf_api import (
    SmfEvent,
    AfEvent,
    AmfEventType,
    EventType,
    NefEvent,
    EventNotifyDataType,
    RanEvent,
    NwdafEvent
)

# Log level
log_level = os.getenv('TOPICS_INIT_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka boostrap server
kafka_bootstrap_server = os.getenv('KAFKA_BOOTSTRAP_SERVER')

shutdown_flag = False


def wait_for_kafka(bootstrap_server: str, timeout: int = 20) -> bool:
    logging.info("Waiting for Kafka to come online...")
    admin_client = AdminClient({'bootstrap.servers': bootstrap_server})

    start_time = time.time()

    while True:
        if shutdown_flag:
            logging.warning("Shutdown signal received. Stopping Kafka wait.")
            raise KeyboardInterrupt("Kafka wait interrupted by shutdown signal")

        try:
            admin_client.list_topics(timeout=10)
            logging.info("Kafka is ready")
            return True
        except Exception as e:
            elapsed_time = time.time() - start_time
            remaining_time = timeout - elapsed_time

            logging.debug(f"Kafka is not ready yet. Error: {e}. Time elapsed: {elapsed_time:.2f}s. "
                          f"Retrying... Remaining time: {remaining_time:.2f}s")

            if elapsed_time >= timeout:
                logging.error("Timeout reached while waiting for Kafka to become ready.")
                raise TimeoutError("Kafka did not become ready within the timeout period.")

            time.sleep(1)


def create_topic(admin_client: AdminClient, topic_name: str) -> None:
    topic = NewTopic(topic_name, num_partitions=1, replication_factor=1)
    fs = admin_client.create_topics([topic])

    for topic, f in fs.items():
        try:
            f.result()
            logging.debug(f"Created Kafka topic '{topic}' successfully")
        except KafkaException as k:
            if k.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                logging.debug(f"Topic '{topic}' already exists")
            else:
                logging.error(f"Failed to create topic '{topic}': {k}")


def get_topic_names(prefix: str, event_type: Type[Enum]) -> list[str]:
    return [f"{prefix}.{event.value}" for event in event_type]


def get_event_exposure_topic_names(prefix: str) -> list[str]:
    topic_list = []

    topic_list.extend(get_topic_names(f"{prefix}.SMF", SmfEvent))
    topic_list.extend(get_topic_names(f"{prefix}.AF", AfEvent))
    topic_list.extend(get_topic_names(f"{prefix}.AMF", AmfEventType))
    topic_list.extend(get_topic_names(f"{prefix}.UPF", EventType))
    topic_list.extend(get_topic_names(f"{prefix}.NEF", NefEvent))
    topic_list.extend(get_topic_names(f"{prefix}.GMLC", EventNotifyDataType))
    topic_list.extend(get_topic_names(f"{prefix}.RAN", RanEvent))

    return topic_list


# Signal handler to stop gracefully
def handle_shutdown_signal(signal_name):
    global shutdown_flag
    logging.info(f"Received {signal_name}. Setting shutdown flag...")
    shutdown_flag = True


def register_signal_handlers():
    signal.signal(signal.SIGINT, lambda signum, frame: handle_shutdown_signal("SIGINT"))
    signal.signal(signal.SIGTERM, lambda signum, frame: handle_shutdown_signal("SIGTERM"))


def main():
    global shutdown_flag

    register_signal_handlers()

    try:
        wait_for_kafka(kafka_bootstrap_server)
        admin_client = AdminClient({'bootstrap.servers': kafka_bootstrap_server})

        topic_list = []
        topic_list.extend(get_topic_names("Control.NwdafEventSubscription", NwdafEvent))
        topic_list.extend(get_topic_names("Data.NwdafEventDelivery", NwdafEvent))
        topic_list.extend(get_event_exposure_topic_names("Control.EventExposureSubscription"))
        topic_list.extend(get_event_exposure_topic_names("Data.EventExposureDelivery"))
        topic_list.extend(get_topic_names("Control.MLModelProvisionSubscription", NwdafEvent))
        topic_list.extend(get_topic_names("Data.MLModelProvisionDelivery", NwdafEvent))
        topic_list.append("Control.DatasetCollectionSubscription")
        topic_list.append("Control.DatasetRetrievalSubscription")
        topic_list.append("Data.DatasetRetrievalDelivery")

        logging.info("Creating all the relevant Kafka topics...")
        for topic_name in topic_list:
            if shutdown_flag:
                logging.warning("Shutdown flag detected during topic creation. Exiting...")
                break
            create_topic(admin_client, topic_name)

        logging.info("All Kafka topics created successfully")
        exit_code = 0
    except KeyboardInterrupt:
        logging.info("Process interrupted by signal.")
        exit_code = 1
    except Exception as e:
        logging.error(f"Kafka topics initialization failed: {e}")
        exit_code = 1

    logging.info("Exiting Kafka initialization.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
