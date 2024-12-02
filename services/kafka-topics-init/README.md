# Kafka Topics Initialization service

This service initializes _Kafka_ topics for a set of _NWDAF_-related events. It ensures that the necessary _Kafka_ topics
are
created and ready for event processing before all the other services are deployed.

## Pre-requisites

* _Python_ ≥ 3.12 (preferably in a virtualenv, or using [Conda](https://anaconda.org/anaconda/conda))
* _confluent-kafka_

## Configuration

The following environment variables are needed to configure this service:

* `TOPICS_INIT_LOG_LEVEL`: Sets the logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR'). Defaults to 'INFO'.
* `KAFKA_BOOTSTRAP_SERVER`: The _Kafka_ bootstrap server address (e.g., 'localhost:9092').