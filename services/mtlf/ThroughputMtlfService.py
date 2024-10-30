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

    def __init__(self):
        super().__init__("mtlf", "kafka:19092", NwdafEvent.UE_LOC_THROUGHPUT)

    @override
    def on_ml_provision_subscription_created(self, sub_id: str, sub: MLEventSubscription):
        notif = MLEventNotif(event=self._handled_analytic_type,
                             m_l_file_addr=MLModelAddr(m_l_model_url="models"))
        logging.info(f"Sending ML Model info to AnLF: {notif.model_dump_json(exclude_unset=True)}")
        self.send_ml_model_provision_notif(sub_id, notif)
