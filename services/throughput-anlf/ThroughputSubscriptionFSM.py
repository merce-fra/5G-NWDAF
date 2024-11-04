from enum import StrEnum
from nwdaf_libcommon.FiniteStateMachine import FiniteStateMachine


class States(StrEnum):
    """
    Enumeration of the states for the throughput subscription finite state machine (FSM).

    Attributes:
        INITIALIZING: The initial state where the subscription is being set up.
        WAITING_FOR_GMLC_NOTIF: The state where the FSM is waiting for notifications from GMLC.
        WAITING_FOR_RAN_NOTIF: The state where the FSM is waiting for notifications from RAN.
        PREDICTING_THROUGHPUT: The state where the FSM is performing throughput prediction.
        SENDING_ANALYTICS_NOTIF: The state where the FSM is sending analytics notifications.
    """
    INITIALIZING = "INITIALIZING",
    WAITING_FOR_GMLC_NOTIF = "WAITING_FOR_GMLC_NOTIF",
    WAITING_FOR_RAN_NOTIF = "WAITING_FOR_RAN_NOTIF",
    PREDICTING_THROUGHPUT = "PREDICTING_THROUGHPUT",
    SENDING_ANALYTICS_NOTIF = "SENDING_ANALYTICS_NOTIF"


class Transitions(StrEnum):
    """
    Enumeration of the transitions for the throughput subscription finite state machine (FSM).

    Attributes:
        INITIALIZATION_DONE: Transition indicating that initialization is complete.
        ALL_NOTIFS_RECEIVED: Transition indicating that all required notifications have been received.
        WAITING_FOR_NOTIFS: Transition indicating that the FSM is waiting for additional notifications.
        PREDICTION_DONE: Transition indicating that throughput prediction is complete.
        ANALYTICS_NOTIF_SENT: Transition indicating that the analytics notification has been sent.
    """
    INITIALIZATION_DONE = "INITIALIZATION_DONE",
    ALL_NOTIFS_RECEIVED = "ALL_NOTIFS_RECEIVED",
    WAITING_FOR_NOTIFS = "WAITING_FOR_NOTIFS",
    PREDICTION_DONE = "PREDICTION_DONE",
    ANALYTICS_NOTIF_SENT = "ANALYTICS_NOTIF_SENT"


class ThroughputSubscriptionFSM(FiniteStateMachine):
    """
    Finite State Machine (FSM) for managing throughput subscription states and transitions.

    This FSM coordinates the states of a throughput subscription process, handling initialization,
    waiting for notifications, predicting throughput, and sending analytics notifications.

    Inherits from the FiniteStateMachine class, initializing with the defined states and transitions.

    States:
        - States.INITIALIZING: The FSM starts in this state while initializing the subscription.
        - States.WAITING_FOR_GMLC_NOTIF: The FSM transitions to this state after initialization, waiting for GMLC notifications.
        - States.WAITING_FOR_RAN_NOTIF: This state is entered when the FSM is waiting for RAN notifications.
        - States.PREDICTING_THROUGHPUT: In this state, the FSM performs throughput predictions.
        - States.SENDING_ANALYTICS_NOTIF: The FSM enters this state to send analytics notifications to GMLC.

    Transitions:
        - Transitions.INITIALIZATION_DONE: Triggers the transition from INITIALIZING to WAITING_FOR_GMLC_NOTIF.
        - Transitions.ALL_NOTIFS_RECEIVED: Moves the FSM to the predicting state after all notifications are received.
        - Transitions.WAITING_FOR_NOTIFS: Allows the FSM to wait for additional notifications if needed.
        - Transitions.PREDICTION_DONE: Transitions the FSM to the sending notifications state once the prediction is done.
        - Transitions.ANALYTICS_NOTIF_SENT: Returns the FSM to the WAITING_FOR_GMLC_NOTIF state after sending analytics notifications.
    """

    def __init__(self):
        super().__init__(
            {
                States.INITIALIZING: {
                    Transitions.INITIALIZATION_DONE: States.WAITING_FOR_GMLC_NOTIF
                },
                States.WAITING_FOR_GMLC_NOTIF: {
                    Transitions.ALL_NOTIFS_RECEIVED: States.PREDICTING_THROUGHPUT,
                    Transitions.WAITING_FOR_NOTIFS: States.WAITING_FOR_RAN_NOTIF
                },
                States.WAITING_FOR_RAN_NOTIF: {
                    Transitions.ALL_NOTIFS_RECEIVED: States.PREDICTING_THROUGHPUT,
                    Transitions.WAITING_FOR_NOTIFS: States.WAITING_FOR_GMLC_NOTIF
                },
                States.PREDICTING_THROUGHPUT: {
                    Transitions.PREDICTION_DONE: States.SENDING_ANALYTICS_NOTIF
                },
                States.SENDING_ANALYTICS_NOTIF: {
                    Transitions.ANALYTICS_NOTIF_SENT: States.WAITING_FOR_GMLC_NOTIF
                }
            },
            States.INITIALIZING
        )