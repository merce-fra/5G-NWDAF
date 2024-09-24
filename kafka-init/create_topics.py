import time
from enum import Enum
from typing import Type
import logging

from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
from nwdaf_api.models.nwdaf_event import NwdafEvent
from nwdaf_api.models.smf_event import SmfEvent
from nwdaf_api.models.af_event import AfEvent
from nwdaf_api.models.amf_event import AmfEventType
from nwdaf_api.models.upf_event import EventType
from nwdaf_api.models.nef_event import NefEvent
from nwdaf_api.models.event_notify_data_type import EventNotifyDataType


def wait_for_kafka(bootstrap_server: str, timeout: int = 20) -> bool:
    logging.info("Waiting for Kafka to come online...")
    admin_client = AdminClient({'bootstrap.servers': bootstrap_server})

    for attempt_count in range(timeout):
        try:
            _topics = admin_client.list_topics(timeout=10)
            logging.info("Kafka is ready")
            return True
        except Exception as e:
            logging.info(f"Attempt {attempt_count + 1}/{timeout} failed: {e}. Retrying...")
            time.sleep(1)

    raise TimeoutError("Kafka did not become ready within the timeout period.")


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

    return topic_list


def main():
    bootstrap_server = "kafka:19092"

    wait_for_kafka(bootstrap_server)

    admin_client = AdminClient({'bootstrap.servers': bootstrap_server})

    topic_list = []

    topic_list.extend(get_topic_names("Control.NwdafEventSubscription", NwdafEvent))
    topic_list.extend(get_topic_names("Data.NwdafEventDelivery", NwdafEvent))
    topic_list.extend(get_event_exposure_topic_names("Control.EventExposureSubscription"))
    topic_list.extend(get_event_exposure_topic_names("Data.EventExposureDelivery"))

    for topic_name in topic_list:
        create_topic(admin_client, topic_name)

    logging.info("All Kafka topics created successfully")


if __name__ == "__main__":
    main()
