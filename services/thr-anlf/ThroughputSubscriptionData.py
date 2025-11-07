# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

from typing import Optional
import numpy as np


class ThroughputSubscriptionData:
    def __init__(self, sub_id: str, supi: str):
        self.sub_id: str = sub_id
        self.supi: str = supi
        self.pending_gmlc_data: Optional[tuple[float, float, float, int]] = None
        self.pending_ran_data: Optional[tuple[float, float]] = None
        self.pending_throughput_prediction: Optional[float] = None
        self.deletion_requested: bool = False

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
