from nwdaf_api.models.nf_type import NFType
from nwdaf_api.models.nnwdaf_events_subscription import NnwdafEventsSubscription
from nwdaf_api.models.nwdaf_event import NwdafEvent
from nwdaf_api.models.event_notify_data_type import EventNotifyDataType
from nwdaf_api.models.input_data import InputData
from nwdaf_api.models.external_client_type import ExternalClientType
from nwdaf_api.models.periodic_event_info import PeriodicEventInfo
from nwdaf_api.models.location_type_requested import LocationTypeRequested
from nwdaf_libcommon.AnlfService import AnlfService
from nwdaf_libcommon.ControlOperationType import ControlOperationType


def get_gmlc_subscription_payload(supi: str) -> InputData:
    return InputData(supi=supi,
                     external_client_type=ExternalClientType.VALUE_ADDED_SERVICES,
                     periodic_event_info=PeriodicEventInfo(reporting_amount=1,
                                                           reporting_interval=5,
                                                           reporting_infinite_ind=True),
                     location_type_requested=LocationTypeRequested.CURRENT_LOCATION)


class ThroughputAnlfService(AnlfService):
    model_id: str

    def __init__(self):
        super().__init__("throughput-anlf",
                         "kafka:19092",
                         {NwdafEvent.UE_LOC_THROUGHPUT},
                         {(NFType.GMLC, EventNotifyDataType.PERIODIC)})

        self.add_analytics_subscription_callback(ControlOperationType.CREATE, self.on_subscription_created)
        self.model_id = self.load_keras_model_file("models/lstm_model.keras")

    def on_subscription_created(self, _sub_id: str, sub: NnwdafEventsSubscription):
        for event_sub in sub.event_subscriptions:
            if event_sub.event != NwdafEvent.UE_LOC_THROUGHPUT:
                continue

            # Send one subscription request per SUPI to the GMLC
            for supi in event_sub.tgt_ue.supis:
                self.queue_event_exposure_subscription(NFType.GMLC, EventNotifyDataType.PERIODIC,
                                                       get_gmlc_subscription_payload(supi))
