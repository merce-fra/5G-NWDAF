import os
import sys
import time
from enum import Enum
from typing import Type
import logging

from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from nwdaf_api.models import (
    NwdafEvent,
    SmfEvent,
    AfEvent,
    AmfEventType,
    EventType,
    NefEvent,
    EventNotifyDataType,
    RanEvent
)

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')


def wait_for_kafka(bootstrap_server: str, timeout: int = 20) -> bool:
    logging.info("Waiting for Kafka to come online...")
    admin_client = AdminClient({'bootstrap.servers': bootstrap_server})

    start_time = time.time()

    while True:
        try:
            # Attempt to list topics to check Kafka's availability
            admin_client.list_topics(timeout=10)
            logging.info("Kafka is ready")
            return True
        except Exception as e:
            elapsed_time = time.time() - start_time
            remaining_time = timeout - elapsed_time

            logging.debug(f"Kafka is not ready yet. Error: {e}. Time elapsed: {elapsed_time:.2f}s. "
                          f"Retrying... Remaining time: {remaining_time:.2f}s")

            # If the timeout is exceeded, raise a TimeoutError
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
    topic_list = []
    for event in event_type:
        topic_list.append(f"{prefix}.{event.value}")
    return topic_list


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


def main():
    bootstrap_server = "kafka:19092"

    try:
        wait_for_kafka(bootstrap_server)
        admin_client = AdminClient({'bootstrap.servers': bootstrap_server})

        topic_list = []
        topic_list.extend(get_topic_names("Control.NwdafEventSubscription", NwdafEvent))
        topic_list.extend(get_topic_names("Data.NwdafEventDelivery", NwdafEvent))
        topic_list.extend(get_event_exposure_topic_names("Control.EventExposureSubscription"))
        topic_list.extend(get_event_exposure_topic_names("Data.EventExposureDelivery"))

        logging.info("Creating all the relevant Kafka topics...")
        for topic_name in topic_list:
            create_topic(admin_client, topic_name)

        logging.info("All Kafka topics created successfully")
        exit_code = 0
    except Exception as e:
        logging.error(f"Kafka topics initialization failed: {e}")
        exit_code = 1

    logging.info("Exiting...")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
