import asyncio
import logging
from enum import Enum
from typing import override, Optional

import numpy as np

from pydantic import BaseModel

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
    RanEventExposureNotification,
    MLEventNotif
)
from nwdaf_libcommon.AnlfService import AnlfService
from ThroughputSubscriptionFSM import ThroughputSubscriptionFSM, States, Transitions


class ThroughputAnlfService(AnlfService):
    """
    A service for handling UE_LOC_THROUGHPUT analytics.
    """

    class ThroughputSubscriptionData:
        def __init__(self, sub_id: str, supi: str):
            self.sub_id: str = sub_id
            self.supi: str = supi
            self.pending_gmlc_data: Optional[tuple[float, float, float, int]] = None
            self.pending_ran_data: Optional[tuple[float, float]] = None
            self.pending_throughput_prediction: Optional[float] = None

    def __init__(self) -> None:
        """
        Initializes the service.
        """
        super().__init__("throughput-anlf",
                         "kafka:19092",
                         NwdafEvent.UE_LOC_THROUGHPUT,
                         {(NFType.GMLC, EventNotifyDataType.PERIODIC), (NFType.RAN, RanEvent.RSRP_INFO)})

        self.subscription_fsms: dict[
            ThroughputAnlfService.ThroughputSubscriptionData, ThroughputSubscriptionFSM] = {}
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

            # Create an FSM for each subscription
            for supi in event_sub.tgt_ue.supis:
                sub_data = self.ThroughputSubscriptionData(sub_id, supi)
                self.subscription_fsms[sub_data] = ThroughputSubscriptionFSM()

    def initialize_subscription(self, sub_id: str, supi: str):
        # Send GMLC and RAN event exposure subscriptions
        logging.info(
            f"Sending a periodic location request to the GMLC for UE '{supi}', CORRELATION_ID={sub_id}")
        self.send_event_exposure_subscription(NFType.GMLC, EventNotifyDataType.PERIODIC,
                                              InputData(supi=supi,
                                                        ldr_reference=sub_id,
                                                        external_client_type=ExternalClientType.VALUE_ADDED_SERVICES,
                                                        periodic_event_info=PeriodicEventInfo(reporting_amount=1,
                                                                                              reporting_interval=10,
                                                                                              reporting_infinite_ind=True),
                                                        location_type_requested=LocationTypeRequested.CURRENT_LOCATION))
        logging.info(f"Sending a RSRP info subscription to the RAN for UE '{supi}', CORRELATION_ID={sub_id}")
        self.send_event_exposure_subscription(NFType.RAN, RanEvent.RSRP_INFO,
                                              RanEventSubscription(event=RanEvent.RSRP_INFO,
                                                                   correlation_id=sub_id,
                                                                   notif_uri="myUri",
                                                                   ue_ids=[supi],
                                                                   periodicity=10))

    def retrieve_sub_data(self, sub_id: str, supi: str) -> Optional[ThroughputSubscriptionData]:
        for sub_data, _fsm in self.subscription_fsms.items():
            if sub_data.sub_id == sub_id and sub_data.supi == supi:
                return sub_data

        return None

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

        sub_id = ue_location_notification.ldr_reference
        supi = ue_location_notification.supi
        sub_data = self.retrieve_sub_data(sub_id, supi)
        if sub_data is not None:
            sub_data.pending_gmlc_data = (latitude, longitude, moving_speed, compass_direction)
        else:
            logging.error(f"Could not find subscription data for ID '{sub_id}' and SUPI '{supi}'")

    def on_ran_rsrp_info_received(self, ran_notification: RanEventExposureNotification):
        for rsrp_info in ran_notification.rsrp_infos:
            logging.info(f"Received new RSRP information from the RAN: UE_ID='{rsrp_info.ue_id}', "
                         f"LTE_RSRP={rsrp_info.lte_rsrp:.2f} dB, "
                         f"NR_SS_RSRP={rsrp_info.nr_ss_rsrp:.2f} dB, "
                         f"CORRELATION_ID={ran_notification.correlation_id}")

            sub_id = ran_notification.correlation_id
            supi = rsrp_info.ue_id
            sub_data = self.retrieve_sub_data(sub_id, supi)
            if sub_data is not None:
                sub_data.pending_ran_data = (rsrp_info.lte_rsrp, rsrp_info.nr_ss_rsrp)
            else:
                logging.error(f"Could not find subscription data for ID '{sub_id}' and SUPI '{supi}'")

    async def ml_model_provision_sub(self):
        while not self._is_ready:
            await asyncio.sleep(0.5)
        logging.info("Sending an ML model provision request to the MTLF")
        self.request_ml_model_provision("throughput-anlf")

    def predict_throughput(self, sub_data: ThroughputSubscriptionData):
        input_data = np.array(
            [[
                sub_data.pending_gmlc_data[0],  # Latitude
                sub_data.pending_gmlc_data[1],  # Longitude
                sub_data.pending_ran_data[0],  # LTE RSRP
                sub_data.pending_ran_data[1],  # NR SS RSRP
                sub_data.pending_gmlc_data[2],  # Moving speed
                sub_data.pending_gmlc_data[3]  # Compass direction
            ]]
        )

        logging.debug(f"About to perform a prediction with the following inputs: {input_data.flatten()}")
        return self.perform_ml_model_prediction(input_data, (1, 1, 6))

    async def fsm_loop(self, tick_duration: float = 0.3):
        while True:
            for sub_data, subscription_fsm in self.subscription_fsms.items():
                match subscription_fsm.current_state:

                    case States.INITIALIZING:
                        self.initialize_subscription(sub_data.sub_id, sub_data.supi)
                        subscription_fsm.transition(Transitions.INITIALIZATION_DONE)

                    case States.WAITING_FOR_GMLC_NOTIF:
                        if sub_data.pending_ran_data is not None and sub_data.pending_gmlc_data is not None:
                            subscription_fsm.transition(Transitions.ALL_NOTIFS_RECEIVED)
                        elif sub_data.pending_ran_data is None:
                            subscription_fsm.transition(Transitions.WAITING_FOR_NOTIFS)
                        elif sub_data.pending_gmlc_data is None:
                            continue

                    case States.WAITING_FOR_RAN_NOTIF:
                        if sub_data.pending_gmlc_data is not None and sub_data.pending_ran_data is not None:
                            subscription_fsm.transition(Transitions.ALL_NOTIFS_RECEIVED)
                        elif sub_data.pending_gmlc_data is None:
                            subscription_fsm.transition(Transitions.WAITING_FOR_NOTIFS)
                        elif sub_data.pending_ran_data is None:
                            continue

                    case States.PREDICTING_THROUGHPUT:
                        predicted_throughput = self.predict_throughput(sub_data)
                        if predicted_throughput is not None:
                            sub_data.pending_throughput_prediction = abs(float(predicted_throughput[0, 0]))
                            sub_data.pending_gmlc_data = None
                            sub_data.pending_ran_data = None
                            subscription_fsm.transition(Transitions.PREDICTION_DONE)

                    case States.SENDING_ANALYTICS_NOTIF:
                        self.send_analytics_notification(sub_data.sub_id,
                                                         EventNotification(event=NwdafEvent.UE_LOC_THROUGHPUT,
                                                                           predicted_throughput_infos=[
                                                                               PredictedThroughputInfo(
                                                                                   supi=sub_data.supi,
                                                                                   throughput=f"{sub_data.pending_throughput_prediction:.2f} Kbps")]))
                        sub_data.pending_throughput_prediction = None
                        subscription_fsm.transition(Transitions.ANALYTICS_NOTIF_SENT)

            await asyncio.sleep(tick_duration)

    @override
    async def start(self):
        self._tasks.append(asyncio.create_task(self.fsm_loop()))
        self._tasks.append(asyncio.create_task(self.ml_model_provision_sub()))
        await super().start()
