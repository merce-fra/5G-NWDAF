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
    MLModelAddr
)
from nwdaf_libcommon.MtlfService import MtlfService
from typing_extensions import override


class ThroughputMtlfService(MtlfService):

    def __init__(self, service_name: str, kafka_bootstrap_server: str):
        super().__init__(service_name, kafka_bootstrap_server, NwdafEvent.UE_LOC_THROUGHPUT)

    @override
    def on_ml_provision_subscription_created(self, sub_id: str, sub: MLEventSubscription):
        notif = MLEventNotif(event=self._handled_analytic_type,
                             m_l_file_addr=MLModelAddr(m_l_model_url="models"))
        logging.info(f"Sending ML Model info to AnLF: {notif.model_dump_json(exclude_unset=True)}")
        self.send_ml_model_provision_notif(sub_id, notif)
