# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

from typing import Any, TypeVar

from nwdaf_libcommon.NwdafService import NwdafService
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.collection import Collection

T = TypeVar("T", bound=BaseModel)


class AdrfService(NwdafService):

    def __init__(self, service_name: str, kafka_bootstrap_server: str, mongo_uri: str, db_name: str = "adrf"):
        super().__init__(service_name, kafka_bootstrap_server)
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

    def get_collection(self, dataset_id: str) -> Collection:
        return self.db[dataset_id]

    def create_update_dataset(self, dataset_id: str, data: BaseModel) -> str:
        collection = self.get_collection(dataset_id)
        result = collection.insert_one(data.model_dump())
        return str(result.inserted_id)

    def read_dataset(self, dataset_id: str, model: type[BaseModel], query: dict[str, Any] = None) -> list[BaseModel]:
        query = query if query else {}
        collection = self.get_collection(dataset_id)
        return [model(**doc) for doc in collection.find(query)]

    def delete_dataset(self, dataset_id: str, query: dict[str, Any] = None) -> int:
        query = query if query else {}
        collection = self.get_collection(dataset_id)
        result = collection.delete_many(query)
        return result.deleted_count

    async def stop(self):
        await super().stop()
        self.client.close()
