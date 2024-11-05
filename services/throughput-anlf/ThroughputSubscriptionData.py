from typing import Optional
import numpy as np


class ThroughputSubscriptionData:
    def __init__(self, sub_id: str, supi: str):
        self.sub_id: str = sub_id
        self.supi: str = supi
        self.pending_gmlc_data: Optional[tuple[float, float, float, int]] = None
        self.pending_ran_data: Optional[tuple[float, float]] = None
        self.pending_throughput_prediction: Optional[float] = None

    def __hash__(self):
        return hash((self.sub_id, self.supi))

    def __eq__(self, other):
        if isinstance(other, ThroughputSubscriptionData):
            return self.sub_id == other.sub_id and self.supi == other.supi
        return False

    def to_input_array(self) -> np.ndarray:
        return np.array([[self.pending_gmlc_data[0], self.pending_gmlc_data[1],
                          self.pending_ran_data[0], self.pending_ran_data[1],
                          self.pending_gmlc_data[2], self.pending_gmlc_data[3]]])
