import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import override

import numpy as np
from keras.src.trainers.trainer import Trainer
from nwdaf_api import MLEventNotif
from nwdaf_api.models import (
    NFType,
    NnwdafEventsSubscription,
    NwdafEvent,
    EventNotifyDataType,
    InputData,
    ExternalClientType,
    PeriodicEventInfo,
    LocationTypeRequested,
    EventNotifyDataExt,
    EventNotification,
    PredictedThroughputInfo,
    RanEvent,
    RanEventSubscription,
    RanEventExposureNotification
)
from nwdaf_libcommon.AnlfService import AnlfService
from pydantic import BaseModel


def get_value_or_default(value, default=0):
    return value if value is not None else default


def get_gmlc_subscription_payload(sub_id: str, supi: str) -> InputData:
    """
    Creates a GMLC subscription payload.

    Args:
        sub_id (str): The subscription ID.
        supi (str): The SUPI (Subscriber Permanent Identifier).

    Returns:
        InputData: The GMLC subscription payload.
    """
    return InputData(supi=supi,
                     ldr_reference=sub_id,
                     external_client_type=ExternalClientType.VALUE_ADDED_SERVICES,
                     periodic_event_info=PeriodicEventInfo(reporting_amount=1,
                                                           reporting_interval=10,
                                                           reporting_infinite_ind=True),
                     location_type_requested=LocationTypeRequested.CURRENT_LOCATION)


def get_ran_subscription_payload(sub_id: str, supi: str) -> RanEventSubscription:
    return RanEventSubscription(event=RanEvent.RSRP_INFO,
                                correlation_id=sub_id,
                                notif_uri="myUri",
                                ue_ids=[supi],
                                periodicity=10)


def get_analytics_notification_payload(supi: str, throughput: float) -> EventNotification:
    """
    Creates an analytics notification payload.

    Args:
        supi (str): The SUPI (Subscriber Permanent Identifier).
        throughput (float): The predicted throughput.

    Returns:
        EventNotification: The analytics notification payload.
    """
    predicted_throughput_info = PredictedThroughputInfo(supi=supi,
                                                        throughput=f"{throughput:.2f} Kbps")
    return EventNotification(event=NwdafEvent.UE_LOC_THROUGHPUT,
                             predicted_throughput_infos=[predicted_throughput_info])


class ThroughputAnlfService(AnlfService):
    """
    A service for handling UE_LOC_THROUGHPUT analytics.
    """

    @dataclass
    class PredictionNotificationParameters:
        latitude: float = 0.0
        longitude: float = 0.0
        moving_speed: float = 0.0
        compass_direction: int = 0
        lte_rsrp: float = 0.0
        nr_ssRsrp: float = 0.0
        correlation_id: str = "id"
        is_ready: bool = False

    pending_predictions = dict[str, PredictionNotificationParameters]

    def __init__(self) -> None:
        """
        Initializes the service.
        """
        super().__init__("throughput-anlf",
                         "kafka:19092",
                         NwdafEvent.UE_LOC_THROUGHPUT,
                         {(NFType.GMLC, EventNotifyDataType.PERIODIC), (NFType.RAN, RanEvent.RSRP_INFO)})

        self.pending_predictions = dict()
        logging.info(f"AnLF service '{self._service_name}' is ready")

    @override
    def on_ml_model_provision_data(self, notification: MLEventNotif):
        logging.info(f"Received ML Model provision data: {notification.model_dump_json(exclude_unset=True)}")
        self.initialize_ml_model(notification.m_l_file_addr.m_l_model_url)

    @override
    def on_analytics_subscription_created(self, sub_id: str, sub: NnwdafEventsSubscription) -> None:
        """
        Handles the creation of a subscription.

        Args:
            sub_id (str): The subscription ID.
            sub (NnwdafEventsSubscription): The subscription.
        """
        for event_sub in sub.event_subscriptions:
            if event_sub.event != NwdafEvent.UE_LOC_THROUGHPUT:
                continue

            event_sub_dict = event_sub.model_dump(exclude_unset=True)
            logging.info(
                f"Created a new analytics subscription for '{event_sub_dict['event'].value}': SUPIs={event_sub_dict['tgt_ue']['supis']}")
            # Send one subscription request per SUPI to the GMLC, and one to the RAN
            for supi in event_sub.tgt_ue.supis:
                logging.info(
                    f"Sending a periodic location request to the GMLC for UE '{supi}', CORRELATION_ID={sub_id}")
                self.send_event_exposure_subscription(NFType.GMLC, EventNotifyDataType.PERIODIC,
                                                      get_gmlc_subscription_payload(sub_id, supi))
                logging.info(f"Sending a RSRP info subscription to the RAN for UE '{supi}', CORRELATION_ID={sub_id}")
                self.send_event_exposure_subscription(NFType.RAN, RanEvent.RSRP_INFO,
                                                      get_ran_subscription_payload(sub_id, supi))

    @override
    def on_event_exposure_data(self, nf_type: NFType, event_type: Enum, data: BaseModel):
        if isinstance(data, EventNotifyDataExt):
            self.on_ue_location_received(EventNotifyDataExt.model_validate(data))
        elif isinstance(data, RanEventExposureNotification):
            self.on_ran_rsrp_info_received(RanEventExposureNotification.model_validate(data))
        else:
            logging.warning(
                f"This AnLF cannot handle this type of notification: {data.model_dump_json(exclude_unset=True)}")

    def on_ue_location_received(self, ue_location_notification: EventNotifyDataExt) -> None:
        """
        Handles the reception of a UE location notification.

        Args:
            ue_location_notification (EventNotifyDataExt): The UE location notification.
        """
        notif_dict = ue_location_notification.model_dump(exclude_unset=True)
        log_message = (f"Received new UE location data from GMLC: SUPI='{notif_dict['supi']}', "
                       f"Location (Lat, Lon)={notif_dict['location_estimate']['anyof_schema_1_validator']['point']['lat']}, "
                       f"{notif_dict['location_estimate']['anyof_schema_1_validator']['point']['lon']}, "
                       f"Speed={notif_dict['velocity_estimate']['anyof_schema_1_validator']['h_speed']:.2f} m/s, "
                       f"Bearing={notif_dict['velocity_estimate']['anyof_schema_1_validator']['bearing']}°, "
                       f"CORRELATION_ID={ue_location_notification.ldr_reference}"
                       )
        logging.info(log_message)
        location_estimate = ue_location_notification.location_estimate.anyof_schema_1_validator
        velocity_estimate = ue_location_notification.velocity_estimate.anyof_schema_1_validator

        # Get all the relevant parameters
        latitude = location_estimate.point.lat
        longitude = location_estimate.point.lon
        moving_speed = velocity_estimate.h_speed
        compass_direction = velocity_estimate.bearing

        if ue_location_notification.supi not in self.pending_predictions:
            self.pending_predictions[ue_location_notification.supi] = self.PredictionNotificationParameters()

        prediction_params = self.pending_predictions[ue_location_notification.supi]
        prediction_params.latitude = latitude
        prediction_params.longitude = longitude
        prediction_params.moving_speed = moving_speed
        prediction_params.compass_direction = compass_direction
        prediction_params.correlation_id = ue_location_notification.ldr_reference

    def on_ran_rsrp_info_received(self, ran_notification: RanEventExposureNotification):
        for rsrp_info in ran_notification.rsrp_infos:
            logging.info(f"Received new RSRP information from the RAN: UE_ID='{rsrp_info.ue_id}', "
                         f"LTE_RSRP={rsrp_info.lte_rsrp:.2f} dB, "
                         f"NR_SS_RSRP={rsrp_info.nr_ss_rsrp:.2f} dB, "
                         f"CORRELATION_ID={ran_notification.correlation_id}")

            if rsrp_info.ue_id not in self.pending_predictions:
                self.pending_predictions[rsrp_info.ue_id] = self.PredictionNotificationParameters()

            prediction_params = self.pending_predictions[rsrp_info.ue_id]
            prediction_params.lte_rsrp = rsrp_info.lte_rsrp
            prediction_params.nr_ssRsrp = rsrp_info.nr_ss_rsrp
            prediction_params.correlation_id = ran_notification.correlation_id

            prediction_params.is_ready = True

    def perform_prediction(self, prediction_params: PredictionNotificationParameters):
        input_data = np.array(
            [[
                prediction_params.latitude,
                prediction_params.longitude,
                prediction_params.lte_rsrp,
                prediction_params.nr_ssRsrp,
                prediction_params.moving_speed,
                prediction_params.compass_direction
            ]]
        )

        logging.debug(f"About to perform a prediction with the following inputs: {input_data.flatten()}")
        return self.perform_ml_model_prediction(input_data, (1, 1, 6))

    async def predict_and_send(self):
        while True:
            prediction_data_to_delete = []
            for supi, parameters in self.pending_predictions.items():
                if parameters.is_ready and parameters.correlation_id is not None:
                    prediction = self.perform_prediction(parameters)
                    if prediction is not None:
                        predicted_throughput = abs(float(prediction[0, 0]))
                        logging.info(
                            f"Predicted throughput for UE '{supi}': {predicted_throughput} Kbps")

                        # Send the analytics notification
                        self.send_analytics_notification(parameters.correlation_id,
                                                         get_analytics_notification_payload(supi,
                                                                                            predicted_throughput))
                        logging.info(f"Sending 'UE_LOC_THROUGHPUT' notification: SUPI='{supi}', "
                                     f"Throughput={abs(predicted_throughput):.2f} Kbps")
                    else:
                        logging.error("Could not perform prediction, the model is unavailable")
                    prediction_data_to_delete.append(supi)

            for supi in prediction_data_to_delete:
                del self.pending_predictions[supi]

            await asyncio.sleep(0.3)

    async def ml_model_provision_sub(self):
        while not self._is_ready:
            await asyncio.sleep(0.5)
        logging.info("Sending an ML model provision request to the MTLF")
        self.request_ml_model_provision("throughput-anlf")

    @override
    async def start(self):
        self._tasks.append(asyncio.create_task(self.predict_and_send()))
        self._tasks.append(asyncio.create_task(self.ml_model_provision_sub()))
        await super().start()
