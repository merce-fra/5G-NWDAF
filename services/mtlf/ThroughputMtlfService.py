from nwdaf_api.models import (
    NwdafEvent
)
from nwdaf_libcommon.MtlfService import MtlfService


class ThroughputMtlfService(MtlfService):

    def __init__(self):
        super().__init__("mtlf", "kafka:19092", NwdafEvent.UE_LOC_THROUGHPUT)

