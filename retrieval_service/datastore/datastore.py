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

import csv
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

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

    async def load_dataset(
        self, airports_ds_path, amenities_ds_path, flights_ds_path, policies_ds_path
    ) -> tuple[
        List[models.Airport],
        List[models.Amenity],
        List[models.Flight],
        List[models.Policy],
    ]:
        airports: List[models.Airport] = []
        with open(airports_ds_path, "r") as f:
            reader = csv.DictReader(f, delimiter=",")
            airports = [models.Airport.model_validate(line) for line in reader]

        amenities: list[models.Amenity] = []
        with open(amenities_ds_path, "r") as f:
            reader = csv.DictReader(f, delimiter=",")
            amenities = [models.Amenity.model_validate(line) for line in reader]

        flights: List[models.Flight] = []
        with open(flights_ds_path, "r") as f:
            reader = csv.DictReader(f, delimiter=",")
            flights = [models.Flight.model_validate(line) for line in reader]
    
        policies: List[models.Policy] = []
        with open(policies_ds_path, "r") as f:
            reader = csv.DictReader(f, delimiter=",")
            policies = [models.Policy.model_validate(line) for line in reader]
        return airports, amenities, flights, policies

    async def export_dataset(
        self,
        airports,
        amenities,
        flights,
        policies,
        airports_new_path,
        amenities_new_path,
        flights_new_path,
        policies_new_path,
    ) -> None:
        with open(airports_new_path, "w") as f:
            col_names = ["id", "iata", "name", "city", "country"]
            writer = csv.DictWriter(f, col_names, delimiter=",")
            writer.writeheader()
            for a in airports:
                writer.writerow(a.model_dump())

        with open(amenities_new_path, "w") as f:
            col_names = [
                "id",
                "name",
                "description",
                "location",
                "terminal",
                "category",
                "hour",
                "sunday_start_hour",
                "sunday_end_hour",
                "monday_start_hour",
                "monday_end_hour",
                "tuesday_start_hour",
                "tuesday_end_hour",
                "wednesday_start_hour",
                "wednesday_end_hour",
                "thursday_start_hour",
                "thursday_end_hour",
                "friday_start_hour",
                "friday_end_hour",
                "saturday_start_hour",
                "saturday_end_hour",
                "content",
                "embedding",
            ]
            writer = csv.DictWriter(f, col_names, delimiter=",")
            writer.writeheader()
            for a in amenities:
                writer.writerow(a.model_dump())

        with open(flights_new_path, "w") as f:
            col_names = [
                "id",
                "airline",
                "flight_number",
                "departure_airport",
                "arrival_airport",
                "departure_time",
                "arrival_time",
                "departure_gate",
                "arrival_gate",
            ]
            writer = csv.DictWriter(f, col_names, delimiter=",")
            writer.writeheader()
            for fl in flights:
                writer.writerow(fl.model_dump())

        with open(policies_new_path, "w") as f:
            col_names = [
                "langchain_id",
                "content",
                "metadata",
                "embedding",
            ]
            writer = csv.DictWriter(f, col_names, delimiter=",")
            writer.writeheader()
            for p in policies:
                writer.writerow(p.model_dump())

    @abstractmethod
    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        pass

    @abstractmethod
    async def export_data(
        self,
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        pass

    @abstractmethod
    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[models.Amenity]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def search_flights_by_number(
        self,
        airline: str,
        flight_number: str,
    ) -> list[models.Flight]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def search_flights_by_airports(
        self,
        date,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def insert_ticket(
        self,
        user_id: str,
        user_name: str,
        user_email: str,
        airline: str,
        flight_number: str,
        departure_airport: str,
        arrival_airport: str,
        departure_time: str,
        arrival_time: str,
    ):
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def list_tickets(
        self,
        user_id: str,
    ) -> list[models.Ticket]:
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
