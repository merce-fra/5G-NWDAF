# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.
from datetime import datetime
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

from typing import Any, TypeVar, Optional
import logging
from enum import Enum

from nwdaf_api import (
    SmfEvent,
    AfEvent,
    AmfEventType,
    EventType,
    NefEvent,
    EventNotifyDataType,
    RanEvent,
    NadrfDataStoreSubscription,
    NadrfDataRetrievalSubscription,
    NadrfDataRetrievalNotification,
    NFType, AmfEventNotification, NsmfEventExposureNotification, MonitoringReport, NefEventExposureNotif,
    AfEventExposureNotif, NrfNotificationData, SACEventReport, UpfNotificationData, EventNotifyData, TimeWindow,
    DataNotification)
from nwdaf_libcommon.NfInfo import NfInfo
from nwdaf_libcommon.ControlOperationType import ControlOperationType
from nwdaf_libcommon.KafkaReadHandler import KafkaSubscriptionMode
from nwdaf_libcommon.KafkaWriteHandler import KafkaWriteMode, KafkaWriteHandler
from nwdaf_libcommon.NwdafService import NwdafService
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.collection import Collection

T = TypeVar("T", bound=BaseModel)


class DataSubInfo(BaseModel):
    nf_type: NFType
    event_type: Enum
    payload: BaseModel


class DatasetRecord(BaseModel):
    type: type[BaseModel]
    payload: BaseModel
    timestamp: datetime


def extract_event_exposure_subscription(data_store_sub: NadrfDataStoreSubscription) -> Optional[DataSubInfo]:
    data_sub = data_store_sub.data_sub
    if data_sub is None:
        return None

    if data_sub.amf_data_sub is not None:
        return DataSubInfo(nf_type=NFType.AMF, event_type=data_sub.amf_data_sub.event_list[0].type,
                           payload=data_sub.amf_data_sub)
    elif data_sub.smf_data_sub is not None:
        return DataSubInfo(nf_type=NFType.SMF, event_type=data_sub.smf_data_sub.event_subs[0].event,
                           payload=data_sub.smf_data_sub)
    elif data_sub.af_data_sub is not None:
        return DataSubInfo(nf_type=NFType.AF, event_type=data_sub.af_data_sub.events_subs[0].event,
                           payload=data_sub.af_data_sub)
    elif data_sub.nef_data_sub is not None:
        return DataSubInfo(nf_type=NFType.NEF, event_type=data_sub.nef_data_sub.events_subs[0].event,
                           payload=data_sub.nef_data_sub)
    elif data_sub.nrf_data_sub is not None:
        return DataSubInfo(nf_type=NFType.NRF, event_type=data_sub.nrf_data_sub.req_notif_events[0],
                           payload=data_sub.nrf_data_sub)
    elif data_sub.nsacf_data_sub is not None:
        return DataSubInfo(nf_type=NFType.NSACF, event_type=data_sub.nsacf_data_sub.event.event_type,
                           payload=data_sub.nsacf_data_sub)
    elif data_sub.upf_data_sub is not None:
        return DataSubInfo(nf_type=NFType.UPF, event_type=data_sub.upf_data_sub.event_list[0].type,
                           payload=data_sub.upf_data_sub)
    elif data_sub.gmlc_data_sub is not None:
        return DataSubInfo(nf_type=NFType.GMLC, event_type=data_sub.gmlc_data_sub.location_type_requested,
                           payload=data_sub.gmlc_data_sub)
    else:
        # Not supported yet
        return None


def extract_event_exposure_timestamp(payload: BaseModel) -> datetime:
    if isinstance(payload, AmfEventNotification):
        return payload.report_list[0].time_stamp
    elif isinstance(payload, NsmfEventExposureNotification):
        return payload.event_notifs[0].time_stamp
    elif isinstance(payload, MonitoringReport):
        return payload.time_stamp
    elif isinstance(payload, NefEventExposureNotif):
        return payload.event_notifs[0].time_stamp
    elif isinstance(payload, AfEventExposureNotif):
        return payload.event_notifs[0].time_stamp
    elif isinstance(payload, NrfNotificationData):
        # No timestamp in this type of notification, return datetime.now() (not the cleanest, but good enough for now)
        return datetime.now()
    elif isinstance(payload, SACEventReport):
        return payload.report.time_stamp
    elif isinstance(payload, UpfNotificationData):
        return payload.notification_items[0].time_stamp
    elif isinstance(payload, EventNotifyData):
        return payload.timestamp_of_location_estimate
    else:
        return datetime.now()


def package_data_notif(record: DatasetRecord) -> Optional[DataNotification]:
    if record.type == AmfEventNotification:
        notif = AmfEventNotification(**record.payload.model_dump())
        return DataNotification(amfEventNotifs=[notif], timeStamp=record.timestamp)
    elif record.type == NsmfEventExposureNotification:
        notif = NsmfEventExposureNotification(**record.payload.model_dump())
        return DataNotification(smfEventNotifs=[notif], timeStamp=record.timestamp)
    elif record.type == MonitoringReport:
        notif = MonitoringReport(**record.payload.model_dump())
        return DataNotification(udmEventNotifs=[notif], timeStamp=record.timestamp)
    elif record.type == NefEventExposureNotif:
        notif = NefEventExposureNotif(**record.payload.model_dump())
        return DataNotification(nefEventNotifs=[notif], timeStamp=record.timestamp)
    elif record.type == AfEventExposureNotif:
        notif = AfEventExposureNotif(**record.payload.model_dump())
        return DataNotification(afEventNotifs=[notif], timeStamp=record.timestamp)
    elif record.type == NrfNotificationData:
        notif = NrfNotificationData(**record.payload.model_dump())
        return DataNotification(nrfEventNotifs=[notif], timeStamp=record.timestamp)
    elif record.type == SACEventReport:
        notif = SACEventReport(**record.payload.model_dump())
        return DataNotification(nsacfEventNotifs=[notif], timeStamp=record.timestamp)
    elif record.type == UpfNotificationData:
        notif = UpfNotificationData(**record.payload.model_dump())
        return DataNotification(upfEventNotifs=[notif], timeStamp=record.timestamp)
    elif record.type == EventNotifyData:
        notif = EventNotifyData(**record.payload.model_dump())
        return DataNotification(gmlcEventNotifs=[notif], timeStamp=record.timestamp)


nf_event_mappings = {NFType.SMF: SmfEvent, NFType.AF: AfEvent, NFType.AMF: AmfEventType, NFType.UPF: EventType,
                     NFType.NEF: NefEvent, NFType.GMLC: EventNotifyDataType, NFType.RAN: RanEvent}


class AdrfService(NwdafService):

    def __init__(self, service_name: str, kafka_bootstrap_server: str, mongo_uri: str, db_name: str = "adrf"):
        super().__init__(service_name, kafka_bootstrap_server)
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.event_exposure_sub_handlers: dict[tuple[NFType, Enum], KafkaWriteHandler] = dict()
        self.current_dataset_ids = set()
        self.dataset_retrieval_delivery_handler: Optional[KafkaWriteHandler] = None

    def get_collection(self, dataset_id: str) -> Collection:
        return self.db[dataset_id]

    def create_update_dataset(self, dataset_id: str, data: BaseModel) -> str:
        collection = self.get_collection(dataset_id)
        timestamp = extract_event_exposure_timestamp(data)
        dataset_record = DatasetRecord(type=type(data), payload=data, timestamp=timestamp)

        result = collection.insert_one(dataset_record.model_dump())
        return str(result.inserted_id)

    def read_dataset(self, dataset_id: str, time_window: TimeWindow) -> list[DatasetRecord]:
        collection = self.get_collection(dataset_id)
        records = [DatasetRecord(**doc) for doc in collection.find()]
        result = []
        for record in records:
            if time_window.start_time <= record.timestamp <= time_window.stop_time:
                result.append(record)
        return result

    def delete_dataset(self, dataset_id: str, query: dict[str, Any] = None) -> int:
        query = query if query else {}
        collection = self.get_collection(dataset_id)
        result = collection.delete_many(query)
        return result.deleted_count

    async def start(self):
        self.initialize_dataset_collection_subscription()
        self.init_event_exposure_sub_handlers()
        self.initialize_event_exposure_delivery()
        self.initialize_dataset_retrieval_subscription()
        self.initialize_dataset_retrieval_delivery()
        await super().start()

    async def stop(self):
        await super().stop()
        self.client.close()

    def init_event_exposure_sub_handlers(self):
        prefix = "Control.EventExposureSubscription"
        for nf_type in nf_event_mappings:
            for event in nf_event_mappings[nf_type]:
                event_exposure_sub_handler = self.add_kafka_write_handler(
                    f"{prefix}.{nf_type.value}.{event.value}",
                    NfInfo.get_event_exposure_notification_type(nf_type), KafkaWriteMode.PAYLOAD)
                self.event_exposure_sub_handlers[(nf_type, event)] = event_exposure_sub_handler

    def on_dataset_collection_subscription_created(self, _sub_id: str, subscription: NadrfDataStoreSubscription):
        event_exp_sub = extract_event_exposure_subscription(subscription)
        if event_exp_sub is None:
            logging.warning("This subscription type cannot be handled by the ADRF, ignoring...")
            return

        # Send the payload and subscribe to the relevant delivery channel, we use the dataSetId as the correlationId for the subscription
        event_exposure_handler = self.event_exposure_sub_handlers[(event_exp_sub.nf_type, event_exp_sub.event_type)]
        if event_exposure_handler is None:
            logging.error(
                f"No available handler for event exposure {event_exp_sub.nf_type.value} {event_exp_sub.event_type.value}, ignoring...")
            return

        event_exposure_handler.enqueue_notification(subscription.data_set_tag.data_set_id, event_exp_sub.payload,
                                                    op_type=ControlOperationType.CREATE)
        self.current_dataset_ids.add(subscription.data_set_tag.data_set_id)

    def initialize_event_exposure_delivery(self):
        prefix = "Data.EventExposureDelivery"
        for nf_type in nf_event_mappings:
            for event in nf_event_mappings[nf_type]:
                model_type = NfInfo.get_event_exposure_notification_type(nf_type)
                event_exposure_sub_handler = self.add_kafka_read_handler(
                    f"{prefix}.{nf_type.value}.{event.value}",
                    model_type,
                    KafkaSubscriptionMode.RECEIVE)

                def event_exposure_callback(payload: model_type):
                    # Retrieve the datasetId (correlationId)
                    datasetId = getattr(payload, NfInfo.get_correlation_id_field_name(nf_type))

                    # Check if we are actively collecting data for this dataset, and forward the payload
                    if datasetId in self.current_dataset_ids:
                        self.on_dataset_data_received(datasetId, payload)

                logging.debug(
                    f"Adding event exposure callback for {nf_type.value} {event.value} (model type {model_type.__name__})")
                event_exposure_sub_handler.add_receive_callback(event_exposure_callback)

    def on_dataset_data_received(self, dataset_id: str, payload: BaseModel):
        logging.info(f"Received new data for dataset '{dataset_id}': {payload.model_dump_json(exclude_unset=True)}")
        self.create_update_dataset(dataset_id, payload)

    def initialize_dataset_collection_subscription(self):
        dataset_collection_sub_handler = self.add_kafka_read_handler(
            f"Control.DatasetCollectionSubscription",
            NadrfDataStoreSubscription, KafkaSubscriptionMode.CRUD)
        dataset_collection_sub_handler.add_crud_event_callback(ControlOperationType.CREATE,
                                                               self.on_dataset_collection_subscription_created)

    def initialize_dataset_retrieval_subscription(self):
        dataset_retrieval_sub_handler = self.add_kafka_read_handler("Control.DatasetRetrievalSubscription",
                                                                    NadrfDataRetrievalSubscription,
                                                                    KafkaSubscriptionMode.CRUD)
        dataset_retrieval_sub_handler.add_crud_event_callback(ControlOperationType.CREATE,
                                                              self.on_dataset_retrieval_subscription_created)

    def initialize_dataset_retrieval_delivery(self):
        dataset_retrieval_delivery_handler = self.add_kafka_write_handler(
            f"Data.DatasetRetrievalDelivery",
            NadrfDataRetrievalNotification, KafkaWriteMode.PAYLOAD)
        self.dataset_retrieval_delivery_handler = dataset_retrieval_delivery_handler

    def on_dataset_retrieval_subscription_created(self, _sub_id: str, subscription: NadrfDataRetrievalSubscription):
        dataset_id = subscription.data_set_id
        dataset_records = self.read_dataset(dataset_id, subscription.time_period)
        for index, record in enumerate(dataset_records):
            notif = NadrfDataRetrievalNotification(notifCorrId=subscription.notif_corr_id, timeStamp=datetime.now(),
                                                   dataNotif=package_data_notif(record))
            if index == len(dataset_records) - 1:
                notif.termination_req = True

            self.dataset_retrieval_delivery_handler.enqueue_notification(dataset_id, notif)
