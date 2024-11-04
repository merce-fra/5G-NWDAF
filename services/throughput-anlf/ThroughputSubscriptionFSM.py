from enum import StrEnum

from nwdaf_libcommon.FiniteStateMachine import FiniteStateMachine


class States(StrEnum):
    INITIALIZING = "INITIALIZING",
    WAITING_FOR_GMLC_NOTIF = "WAITING_FOR_GMLC_NOTIF",
    WAITING_FOR_RAN_NOTIF = "WAITING_FOR_RAN_NOTIF",
    PREDICTING_THROUGHPUT = "PREDICTING_THROUGHPUT",
    SENDING_ANALYTICS_NOTIF = "SENDING_ANALYTICS_NOTIF"


class Transitions(StrEnum):
    INITIALIZATION_DONE = "INITIALIZATION_DONE",
    ALL_NOTIFS_RECEIVED = "ALL_NOTIFS_RECEIVED",
    WAITING_FOR_NOTIFS = "WAITING_FOR_NOTIFS",
    PREDICTION_DONE = "PREDICTION_DONE",
    ANALYTICS_NOTIF_SENT = "ANALYTICS_NOTIF_SENT"


class ThroughputSubscriptionFSM(FiniteStateMachine):

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
