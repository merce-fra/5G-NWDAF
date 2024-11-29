# 5G NWDAF

This project implements a microservices-based _5G_ _NWDAF_ (_Network Data Analytics Function_) following the
_3GPP_ specifications.

It is developed entirely in _Python_ and uses _Apache Kafka_ for internal communication. Each microservice is running in
its own _Docker_ container, and the whole system is deployed with _Docker Compose_.

The project is structured to maximize modularity and reusability through two libraries:  `nwdaf-api` and
`nwdaf-libcommon`.

## Clone

In order to clone the current repository on your local environment, run the following commands:

```bash
git clone git@merce-gitlab.fr-merce.mee.com:artur/5g-nwdaf.git
```

For this clone operation to succeed, you should have already set up an _SSH_ key for authentication on your _Gitlab_
profile and made sure the right _SSH_ configuration is present on your local
environment. [This tutorial](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/gitlab-ssh-config/-/blob/main/README.md)
explains how to
do it.

You can then navigate to the freshly cloned repository to access the codebase:

```bash
cd ./5g-nwdaf
```

## Dependencies

The project leverages two internal libraries:

1. `nwdaf-api`, a package based on
   the [nwdaf-3gpp-apis](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-3gpp-apis) repository
    * Contains model classes generated from official _3GPP_ _OpenAPI_ _YAML_ files.
    * Primarily used for message payloads, ensuring compliance with _3GPP_-defined data structures.
    * Release managed by _CI/CD_ pipelines and distributed via the
      _[MERCE Python Packages](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/python-packages/-/packages)_ internal
      registry.

2. `nwdaf-libcommon`, a package based on
   the [nwdaf-libcommon](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon) repository
    * Provides platform-level code to streamline the development of new _NWDAF_ services (e.g., _AnLF_, _MTLF_).
    * Includes utility functions, common patterns, and boilerplate code to minimize the effort required for
      implementing new microservices.
    * Release managed by _CI/CD_ pipelines and distributed via the
      _[MERCE Python Packages](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/python-packages/-/packages)_ internal
      registry.

## Overview

The system consists of multiple microservices, each with a specific role within the NWDAF ecosystem.

* [**API Gateway**](./services/api-gateway): Acts as the single point of entry for incoming _3GPP_-compliant requests,
  handling analytics
  subscriptions and coordinating the flow between services. It is based on
  the [
  _ApiGatewayService_](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon/-/blob/main/src/nwdaf_libcommon/ApiGatewayService.py)
  class from `nwdaf-libcommon`.

* [**Throughput AnLF**](./services/thr-anlf): Computes _UE_LOC_THROUGHPUT_ analytics using data collected from _GMLC_
  and _RAN_, and an _LSTM_
  model that
  predicts throughput from location data. It is based on
  the [
  _AnlfService_](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon/-/blob/main/src/nwdaf_libcommon/AnlfService.py)
  class from `nwdaf-libcommon`.
* [**Throughput MTLF**](./services/thr-mtlf): Provides and manages the _ML_ model used by the _Throughput AnLF_ to make
  inferences, ensuring
  the model remains
  up-to-date and efficient. It is based on
  the [
  _MtlfService_](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon/-/blob/main/src/nwdaf_libcommon/MtlfService.py)
  class from `nwdaf-libcommon`.

> **NB**: The _UE_LOC_THROUGHPUT_ analytics type and the _RAN Event Exposure_ service are not defined in the _3GPP_
> specifications, and have been implemented here for example purposes.


In addition to these main _NWDAF_ services, a whole set of additional services are deployed in the system:

* [**GMLC**](./nf-stubs/gmlc): a _GMLC_ stub serving an event exposure endpoint compliant with _3GPP_ specifications. It
  can either
  generate random location data, or provide data received from the _CSV File Player_.
* [**RAN**](./nf-stubs/ran): a _RAN_ stub serving a non-_3GPP_-compliant event exposure endpoint. It can either generate
  random _RSRP_ data, or provide data received from the _CSV File Player_.
* [**CSV File Player**](./nf-stubs/csv_file_player): a service that reads a _CSV_ file line by line and pushed the data to
  other services (in our case, the _GMLC_ and the _RAN_ stubs). If this service is not running, the _NF_ stubs will use
  randomly
  generated data.
* [**Notification Client**](./nf-stubs/notification-client): a service that can receive analytics notifications, display
  their content and push it to other services (e.g., _Prometheus_, _Grafana_, etc.)

Finally, a few technical services are also deployed:

* **Zookeeper**:  centralized server for maintaining configuration information, naming, and providing distributed
  synchronization and group services. _Kafka_ uses _Zookeeper_ under the hood, it is therefore mandatory to deploy it in
  order to use _Kafka_.
* **Kafka**: an event-streaming platform enabling topic-based producer/consumer interactions. In this project, _Kafka_
  is
  used for internal messaging between microservices.
* **[Kafka Topics Init](./services/kafka-topics-init)**: A service that initializes all the _Kafka_ topics in advance
  before all the _NWDAF_ services are launched. It is necessary to initialize these topics in advance to avoid
  time-consuming re-balancing operations when a message is first sent on a given topic.
* **Grafana**: A data visualization tool that can read data from _HTTP_ endpoints and display it. In our case, it is
  used to read data pushed to _Prometheus_ by the _Notification Client_.
* **Prometheus**: A metrics storage system that provides easy to use data push/pull mechanisms. In our case, it is
  simply used as a middle-man between the _Notification Client_ and _Grafana_.

## Configure

### Package repository access

A token to access the _MERCE Package Registry_ is required to build and deploy the
microservices. [This tutorial](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/python-packages#create-you-access-token)
explains how to create such a token.

You should then export the following environment variables:

```bash
export GITLAB_TOKEN_NAME=<gitlab_token_name>
export GITLAB_TOKEN_VALUE=<gitlab_token_value>
```

In these commands, _<gitlab_token_name>_ and _<gitlab_token_value>_ should be replaced by the relevant values. You can
also add these exports in your `.bashrc` in order to avoid doing this step for every new session.

### Services configuration

Each service's hostname, port and log level can be configured through the [.env](./.env) file that will be used by the
_Docker
Compose_ deployment. For example, this is the default _API Gateway_'s configured values:

```ini
API_GW_SERVICE_NAME = api-gateway
API_GW_SERVICE_PORT = 5000
API_GW_LOG_LEVEL = INFO
```

## Build

To build all the microservices, only one command is needed:

```bash
docker compose build
```

If re-building the containers from scratch is needed, the `--no-cache` option can be passed to the command.

## Deploy

To deploy the _NWDAF_, only one command is needed:

```bash
docker compose up
```

If everything goes well, your _NWDAF_ and all the aforementioned additional services should be deployed and functional.

## Test

Here is an example analytics subscription payload that can be sent to the _NWDAF_ in order to test it:

> **POST 127.0.0.1:5000/nnwdaf-eventssubscription/v1/subscriptions**

```json
{
  "eventSubscriptions": [
    {
      "event": "UE_LOC_THROUGHPUT",
      "tgtUe": {
        "supis": [
          "imsi-208890000000003"
        ]
      }
    }
  ],
  "notificationURI": "http://notification-client:8181/analytics-notification",
  "notifCorrId": "test"
}
```

The _NWDAF_ should reply with a _3GPP_-compliant response, and analytics notifications should be sent periodically to the
_Notification Client_ on port _8181_.
