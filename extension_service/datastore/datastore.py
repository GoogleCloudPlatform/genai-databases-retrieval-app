# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

import models


class AbstractConfig(ABC):
    kind: str


C = TypeVar("C", bound=AbstractConfig)


class classproperty:
    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)


class Client(ABC, Generic[C]):
    @classproperty
    @abstractmethod
    def kind(cls):
        pass

    @classmethod
    @abstractmethod
    async def create(cls, config: C) -> "Client":
        pass

    @abstractmethod
    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
    ) -> None:
        pass

    @abstractmethod
    async def export_data(
        self,
    ) -> tuple[list[models.Airport], list[models.Amenity], list[models.Flight]]:
        pass

    @abstractmethod
    async def get_airport(self, id: int) -> Optional[models.Airport]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> Optional[list[models.Amenity]]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def get_flight(self, flight_id: int) -> Optional[list[models.Flight]]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def get_flight_number(
        self, airline: str, flight_number: int
    ) -> Optional[list[models.Flight]]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def search_flights(
        self,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Optional[list[models.Flight]]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def close(self):
        pass


async def create(config: AbstractConfig) -> Client:
    for cls in Client.__subclasses__():
        s = f"{config.kind} == {cls.kind}"
        if config.kind == cls.kind:
            return await cls.create(config)  # type: ignore
    raise TypeError(f"No clients of kind '{config.kind}'")
