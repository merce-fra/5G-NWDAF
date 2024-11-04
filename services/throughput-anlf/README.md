# Throughput AnLF

## Overview

The `ThroughputAnlfService` is a service designed to handle _UE_ throughput analytics in an _NWDAF_ microservice-based
architecture. It uses an [_LSTM_ model](https://merce-gitlab.fr-merce.mee.com/gitlab/merckube/merckube-lstm) to predict
a throughput value based on data collected from the _[GMLC](https://en.wikipedia.org/wiki/GMLC)_ and the
_[RAN](https://en.wikipedia.org/wiki/Radio_access_network)_.

## Pre-requisites

To use the `ThroughputAnlfService`, you need to have the following pre-requisites:

* _Python_ ≥ 3.12 (preferably in a _virtualenv_, or using [Conda](https://anaconda.org/anaconda/conda))

You can then install the required third-party library with this command:

```bash
pip install -r requirements.txt
````

# How does it work?

Basic _AnLF_ operations (analytics subscription CRUD operations, event exposure mechanics, analytics delivery, _ML_
model provisioning, etc.) are
inherited from
the [AnlfService](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon/-/blob/main/src/nwdaf_libcommon/AnlfService.py)
class from the [nwdaf-libcommon](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon) library.

Finite-state machines are used to handle subscriptions concurrently. Each subscription has its own [FSM](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon/-/blob/main/src/nwdaf_libcommon/FiniteStateMachine.py) with the
following states and transitions:

```mermaid
stateDiagram
    [*] --> INITIALIZING
    INITIALIZING --> WAITING_FOR_GMLC_NOTIF: INITIALIZATION_DONE
    WAITING_FOR_GMLC_NOTIF --> PREDICTING_THROUGHPUT: ALL_NOTIFS_RECEIVED
    WAITING_FOR_GMLC_NOTIF --> WAITING_FOR_RAN_NOTIF: WAITING_FOR_NOTIFS
    WAITING_FOR_RAN_NOTIF --> PREDICTING_THROUGHPUT: ALL_NOTIFS_RECEIVED
    WAITING_FOR_RAN_NOTIF --> WAITING_FOR_GMLC_NOTIF: WAITING_FOR_NOTIFS
    PREDICTING_THROUGHPUT --> SENDING_ANALYTICS_NOTIF: PREDICTION_DONE
    SENDING_ANALYTICS_NOTIF --> WAITING_FOR_GMLC_NOTIF: ANALYTICS_NOTIF_SENT
```