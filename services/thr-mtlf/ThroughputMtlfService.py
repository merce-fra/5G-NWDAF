# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

import logging

from nwdaf_api.models import (
    NwdafEvent,
    MLEventSubscription,
    MLEventNotif,
    MLModelAddr,
    NadrfDataStoreSubscription,
    DataSetTag,
    DataSubscription,
    InputData,
    ExternalClientType,
    PeriodicEventInfo,
    LocationTypeRequested
)
from nwdaf_libcommon.MtlfService import MtlfService
from typing_extensions import override


class ThroughputMtlfService(MtlfService):

    def __init__(self, service_name: str, kafka_bootstrap_server: str):
        super().__init__(service_name, kafka_bootstrap_server, NwdafEvent.UE_LOC_THROUGHPUT)

    @override
    def on_ml_provision_subscription_created(self, sub_id: str, sub: MLEventSubscription):
        # Send the ML model info back to the AnLF
        notif = MLEventNotif(event=self._handled_analytic_type,
                             mLFileAddr=MLModelAddr(mLModelUrl="models"))
        logging.info(f"Sending ML Model info to AnLF: {notif.model_dump_json(exclude_unset=True)}")
        self.send_ml_model_provision_notif(sub_id, notif)

        # Also, send a dataset collection subscription to the ADRF
        dataSetId = "throughput_dataset"
        dataset_sub = NadrfDataStoreSubscription(dataSetTag=DataSetTag(dataSetId=dataSetId),
                                                 dataSub=DataSubscription(gmlcDataSub=InputData(supi="imsi-abcde",
                                                                                                ldrReference=dataSetId,
                                                                                                externalClientType=ExternalClientType.VALUE_ADDED_SERVICES,
                                                                                                periodicEventInfo=PeriodicEventInfo(
                                                                                                    reportingAmount=1,
                                                                                                    reportingInterval=10,
                                                                                                    reportingInfiniteInd=True),
                                                                                                locationTypeRequested=LocationTypeRequested.CURRENT_LOCATION)))
        self.send_dataset_collection_subscription(dataSetId, dataset_sub)
