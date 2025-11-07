# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

import asyncio
import logging
from enum import Enum
from typing import override, Optional

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
from nwdaf_libcommon.ControlOperationType import ControlOperationType
from nwdaf_libcommon.KafkaPayload import KafkaPayload
from pydantic import BaseModel

from ThroughputSubscriptionFSM import ThroughputSubscriptionFSM, States, Transitions
from ThroughputSubscriptionData import ThroughputSubscriptionData
from ThroughputSubscriptionRegistry import ThroughputSubscriptionRegistry


class ThroughputAnlfService(AnlfService):
    """
    An AnLF service for handling UE_LOC_THROUGHPUT analytics.
    """

    def __init__(self, service_name: str, kafka_botstrap_server: str):
        """
        Initializes the service.
        """
        super().__init__(service_name,
                         kafka_botstrap_server,
                         NwdafEvent.UE_LOC_THROUGHPUT,
                         {(NFType.GMLC, EventNotifyDataType.PERIODIC), (NFType.RAN, RanEvent.RSRP_INFO)})

        self.subscription_registry = ThroughputSubscriptionRegistry()
        self.current_subs: set[str] = set()
        logging.info(f"AnLF service '{self._service_name}' is ready")

    @override
    def on_ml_model_provision_data(self, notification: MLEventNotif):
        logging.info(f"Received ML Model provision data: {notification.model_dump_json(exclude_unset=True)}")
        self.initialize_ml_model(notification.m_l_file_addr.m_l_model_url)

    @override
    def on_analytics_subscription_created(self, sub_id: str, sub: NnwdafEventsSubscription):
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
                self.subscription_registry.add_subscription(ThroughputSubscriptionData(sub_id, supi),
                                                            ThroughputSubscriptionFSM())

            self.current_subs.add(sub_id)

    @override
    def on_analytics_subscription_deleted(self, sub_id: str, sub: NnwdafEventsSubscription):
        """
        Handles the deletion of a subscription.

        Args:
            sub_id (str): The subscription ID.
            sub (NnwdafEventsSubscription): The subscription.
        """
        for event_sub in sub.event_subscriptions:
            if event_sub.event != NwdafEvent.UE_LOC_THROUGHPUT:
                continue

            for supi in event_sub.tgt_ue.supis:
                self.subscription_registry.mark_for_deletion(sub_id, supi)

    def initialize_subscription(self, sub_id: str, supi: str):
        # Send GMLC and RAN event exposure subscriptions
        logging.info(
            f"Sending a periodic location request to the GMLC for UE '{supi}', CORRELATION_ID={sub_id}")
        self.send_event_exposure_subscription(NFType.GMLC, EventNotifyDataType.PERIODIC,
                                              KafkaPayload(resource_id=ControlOperationType.CREATE,
                                                           resource_data=InputData(supi=supi,
                                                                                   ldrReference=sub_id,
                                                                                   externalClientType=ExternalClientType.VALUE_ADDED_SERVICES,
                                                                                   periodicEventInfo=PeriodicEventInfo(
                                                                                       reportingAmount=1,
                                                                                       reportingInterval=10,
                                                                                       reportingInfiniteInd=True),
                                                                                   locationTypeRequested=LocationTypeRequested.CURRENT_LOCATION)))
        logging.info(f"Sending a RSRP info subscription to the RAN for UE '{supi}', CORRELATION_ID={sub_id}")
        self.send_event_exposure_subscription(NFType.RAN, RanEvent.RSRP_INFO,
                                              KafkaPayload(resource_id=ControlOperationType.CREATE,
                                                           resource_data=RanEventSubscription(event=RanEvent.RSRP_INFO,
                                                                                              correlationId=sub_id,
                                                                                              notifUri="myUri",
                                                                                              ueIds=[supi],
                                                                                              periodicity=10)))

    @override
    def on_event_exposure_data(self, nf_type: NFType, event_type: Enum, data: BaseModel):
        if isinstance(data, EventNotifyDataExt):
            self.on_ue_location_received(EventNotifyDataExt.model_validate(data))
        elif isinstance(data, RanEventExposureNotification):
            self.on_ran_rsrp_info_received(RanEventExposureNotification.model_validate(data))
        else:
            logging.warning(
                f"This AnLF cannot handle this type of notification: {data.model_dump_json(exclude_unset=True)}")

    def on_ue_location_received(self, ue_location_notification: EventNotifyDataExt):
        """
        Handles the reception of a UE location notification.

        Args:
            ue_location_notification (EventNotifyDataExt): The UE location notification.
        """
        if ue_location_notification.ldr_reference not in self.current_subs:
            return

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
        sub_data = self.subscription_registry.get_subscription_data(sub_id, supi)
        if sub_data is not None:
            sub_data.pending_gmlc_data = (latitude, longitude, moving_speed, compass_direction)
        else:
            logging.error(f"Could not find subscription data for ID '{sub_id}' and SUPI '{supi}'")

    def on_ran_rsrp_info_received(self, ran_notification: RanEventExposureNotification):
        if ran_notification.correlation_id not in self.current_subs:
            return

        for rsrp_info in ran_notification.rsrp_infos:
            logging.info(f"Received new RSRP information from the RAN: UE_ID='{rsrp_info.ue_id}', "
                         f"LTE_RSRP={rsrp_info.lte_rsrp:.2f} dB, "
                         f"NR_SS_RSRP={rsrp_info.nr_ss_rsrp:.2f} dB, "
                         f"CORRELATION_ID={ran_notification.correlation_id}")

            sub_id = ran_notification.correlation_id
            supi = rsrp_info.ue_id
            sub_data = self.subscription_registry.get_subscription_data(sub_id, supi)
            if sub_data is not None:
                sub_data.pending_ran_data = (rsrp_info.lte_rsrp, rsrp_info.nr_ss_rsrp)
            else:
                logging.error(f"Could not find subscription data for ID '{sub_id}' and SUPI '{supi}'")

    async def ml_model_provision_sub(self):
        while not self._is_ready:
            await asyncio.sleep(0.5)
        logging.info("Sending an ML model provision request to the MTLF")
        self.request_ml_model_provision("thr-anlf")

    def predict_throughput(self, sub_data: ThroughputSubscriptionData) -> Optional[float]:
        input_data = sub_data.to_input_array()

        logging.debug(f"About to perform a prediction with the following inputs: {input_data.flatten()}")
        prediction = self.perform_ml_model_prediction(input_data, (1, 1, 6))
        return None if prediction is None else abs(float(prediction[0, 0]))

    async def fsm_loop(self, tick_duration: float = 0.3):
        while True:
            for sub_data in self.subscription_registry.get_all_subscriptions():
                subscription_fsm = self.subscription_registry.get_fsm(sub_data)
                match subscription_fsm.current_state:

                    case States.INITIALIZING:
                        if sub_data.deletion_requested:
                            subscription_fsm.transition(Transitions.DELETION_REQUESTED)
                        else:
                            self.initialize_subscription(sub_data.sub_id, sub_data.supi)
                            subscription_fsm.transition(Transitions.INITIALIZATION_DONE)

                    case States.WAITING_FOR_GMLC_NOTIF | States.WAITING_FOR_RAN_NOTIF:
                        if sub_data.deletion_requested:
                            subscription_fsm.transition(Transitions.DELETION_REQUESTED)
                        elif sub_data.pending_ran_data and sub_data.pending_gmlc_data:
                            subscription_fsm.transition(Transitions.ALL_NOTIFS_RECEIVED)
                        else:
                            subscription_fsm.transition(Transitions.WAITING_FOR_NOTIFS)
                            continue

                    case States.PREDICTING_THROUGHPUT:
                        if sub_data.deletion_requested:
                            subscription_fsm.transition(Transitions.DELETION_REQUESTED)
                        else:
                            predicted_throughput = self.predict_throughput(sub_data)
                            if predicted_throughput is not None:
                                sub_data.pending_throughput_prediction = predicted_throughput
                                sub_data.pending_gmlc_data = None
                                sub_data.pending_ran_data = None
                                subscription_fsm.transition(Transitions.PREDICTION_DONE)

                    case States.SENDING_ANALYTICS_NOTIF:
                        if sub_data.deletion_requested:
                            subscription_fsm.transition(Transitions.DELETION_REQUESTED)
                        self.send_analytics_notification(sub_data.sub_id,
                                                         EventNotification(event=NwdafEvent.UE_LOC_THROUGHPUT,
                                                                           predictedThroughputInfos=[
                                                                               PredictedThroughputInfo(
                                                                                   supi=sub_data.supi,
                                                                                   throughput=f"{sub_data.pending_throughput_prediction:.2f} Mbps")]))
                        sub_data.pending_throughput_prediction = None
                        subscription_fsm.transition(Transitions.ANALYTICS_NOTIF_SENT)

                    case States.DELETING:
                        # Delete stuff
                        self.subscription_registry.remove_subscription(sub_data.sub_id, sub_data.supi)

            await asyncio.sleep(tick_duration)

    @override
    async def start(self):
        self._tasks.append(asyncio.create_task(self.fsm_loop()))
        self._tasks.append(asyncio.create_task(self.ml_model_provision_sub()))
        await super().start()
