# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

from typing import Optional

from ThroughputSubscriptionData import ThroughputSubscriptionData
from ThroughputSubscriptionFSM import ThroughputSubscriptionFSM

class ThroughputSubscriptionRegistry:
    def __init__(self):
        self._subscription_fsms = {}
        self._subscription_data_lookup = {}

    def add_subscription(self, sub_data: ThroughputSubscriptionData, fsm: ThroughputSubscriptionFSM):
        self._subscription_fsms[sub_data] = fsm
        self._subscription_data_lookup[(sub_data.sub_id, sub_data.supi)] = sub_data

    def get_fsm(self, sub_data: ThroughputSubscriptionData) -> Optional[ThroughputSubscriptionFSM]:
        return self._subscription_fsms.get(sub_data)

    def get_subscription_data(self, sub_id: str, supi: str) -> Optional[ThroughputSubscriptionData]:
        return self._subscription_data_lookup.get((sub_id, supi))

    def remove_subscription(self, sub_id: str, supi: str):
        sub_data = self.get_subscription_data(sub_id, supi)
        if sub_data:
            self._subscription_fsms.pop(sub_data, None)
            self._subscription_data_lookup.pop((sub_id, supi), None)

    def get_all_subscriptions(self) -> list[ThroughputSubscriptionData]:
        return list(self._subscription_fsms.keys())