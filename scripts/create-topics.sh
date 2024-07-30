#!/bin/bash


# Function to create a Kafka topic
create-topic() {
  kafka-topics \
  --bootstrap-server kafka:19092 \
  --topic "$1" \
  --replication-factor 1 \
  --partitions 1 \
  --create

  echo "Created Kafka topic '$1' successfully"
}

# First, wait for Kafka to be ready
echo "Waiting for Kafka to come online..."
cub kafka-ready -b kafka:19092 1 20



# Create Kafka topics
create-topic "api_gateway_test"
create-topic "Control.NwdafEventSubscription.ABNORMAL_BEHAVIOUR"
create-topic "Control.EventExposureSubscription.SMF.PDU_SES_EST"
create-topic "Data.EventExposureDelivery.SMF.PDU_SES_EST"
create-topic "Data.NwdafEventDelivery.ABNORMAL_BEHAVIOUR"

echo "All Kafka topics created successfully"

exit 0