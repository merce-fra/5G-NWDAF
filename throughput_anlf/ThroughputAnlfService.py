import random

import numpy
from nwdaf_api.models.nf_type import NFType
from nwdaf_api.models.nnwdaf_events_subscription import NnwdafEventsSubscription
from nwdaf_api.models.nwdaf_event import NwdafEvent
from nwdaf_api.models.event_notify_data_type import EventNotifyDataType
from nwdaf_api.models.input_data import InputData
from nwdaf_api.models.external_client_type import ExternalClientType
from nwdaf_api.models.periodic_event_info import PeriodicEventInfo
from nwdaf_api.models.location_type_requested import LocationTypeRequested
from nwdaf_api.models.event_notify_data_ext import EventNotifyDataExt
from nwdaf_api.models.event_notification import EventNotification
from nwdaf_api.models.predicted_throughput_info import PredictedThroughputInfo
from nwdaf_libcommon.AnlfService import AnlfService
from nwdaf_libcommon.ControlOperationType import ControlOperationType


def get_gmlc_subscription_payload(sub_id: str, supi: str) -> InputData:
    return InputData(supi=supi,
                     ldr_reference=sub_id,
                     external_client_type=ExternalClientType.VALUE_ADDED_SERVICES,
                     periodic_event_info=PeriodicEventInfo(reporting_amount=1,
                                                           reporting_interval=5,
                                                           reporting_infinite_ind=True),
                     location_type_requested=LocationTypeRequested.CURRENT_LOCATION)


def get_analytics_notification_payload(supi: str, throughput: float) -> EventNotification:
    predicted_throughput_info = PredictedThroughputInfo(supi=supi,
                                                        throughput=f"{abs(throughput):.2f} Kbps")
    return EventNotification(event=NwdafEvent.UE_LOC_THROUGHPUT,
                             predicted_throughput_infos=[predicted_throughput_info])


class ThroughputAnlfService(AnlfService):
    model_id: str

    def __init__(self):
        super().__init__("throughput-anlf",
                         "kafka:19092",
                         {NwdafEvent.UE_LOC_THROUGHPUT},
                         {(NFType.GMLC, EventNotifyDataType.PERIODIC)})

        self.add_analytics_subscription_callback(ControlOperationType.CREATE, self.on_subscription_created)
        self.model_id = self.load_keras_model_file("models/lstm_model.keras")

        self.set_event_exposure_data_callback(NFType.GMLC, EventNotifyDataType.PERIODIC, self.on_ue_location_received)

    def on_subscription_created(self, sub_id: str, sub: NnwdafEventsSubscription):
        for event_sub in sub.event_subscriptions:
            if event_sub.event != NwdafEvent.UE_LOC_THROUGHPUT:
                continue

            # Send one subscription request per SUPI to the GMLC
            for supi in event_sub.tgt_ue.supis:
                self.queue_event_exposure_subscription(NFType.GMLC, EventNotifyDataType.PERIODIC,
                                                       get_gmlc_subscription_payload(sub_id, supi))

    def on_ue_location_received(self, ue_location_notification: EventNotifyDataExt):
        location_estimate = ue_location_notification.location_estimate.anyof_schema_1_validator
        velocity_estimate = ue_location_notification.velocity_estimate.anyof_schema_1_validator

        # Get all the relevant parameters
        latitude = location_estimate.point.lat
        longitude = location_estimate.point.lon
        moving_speed = velocity_estimate.h_speed
        compass_direction = velocity_estimate.bearing

        # Randomly generate the remaining RAN parameters
        lte_rsrp = random.randint(-140, -44)
        nr_ssRsrp = random.uniform(-139.0, -68.0)

        # Make a prediction using the Keras model previously loaded
        input_data = numpy.array([[latitude, longitude, lte_rsrp, nr_ssRsrp, moving_speed, compass_direction]])
        input_data = input_data.reshape((1, 1, 6))
        predicted_throughput = self.predict(self.model_id, input_data)[0, 0]

        # Send the analytics notification
        self.queue_analytics_notification(ue_location_notification.ldr_reference,
                                          get_analytics_notification_payload(ue_location_notification.supi,
                                                                             predicted_throughput))
