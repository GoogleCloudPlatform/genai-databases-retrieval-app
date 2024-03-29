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
from typing import Any, Generic, List, Optional, TypeVar

from google.cloud.storage import Client as StorageClient
from pydantic import BaseModel

import models
from helpers import UIFriendlyLogger


class AbstractConfig(ABC):
    kind: str


C = TypeVar("C", bound=AbstractConfig)
T = TypeVar("T", bound=BaseModel)


class classproperty:
    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)


class CSVStreamer(Generic[T]):
    read = 0
    done_reading = False

    def __init__(self, bucket, blob_path, max_rows, validator):
        self.file = bucket.blob(blob_path).open("rt", encoding="utf-8")
        self.csv_reader = csv.DictReader(self.file, delimiter=",")
        self.validator = validator
        self.max_rows = max_rows

    def read_next_n(self, n: int) -> List[T]:
        rows = []
        # If max rows is set, default, only fetch up to that
        fetch_count = (
            min(self.max_rows - self.read, n) if self.max_rows is not None else n
        )
        try:
            for _ in range(fetch_count):
                rows.append(next(self.csv_reader))
        except StopIteration:
            # End of file on GCS
            self.done_reading = True
            pass
        self.read = self.read + len(rows)
        # Only read up to max rows
        if self.max_rows is not None and self.read >= self.max_rows:
            self.done_reading = True
        return [self.validator(row) for row in rows]

    def is_done(self):
        return self.done_reading

    def close(self):
        self.file.close()


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
        self,
        bucket_path,
        airports_ds_path,
        amenities_ds_path,
        policies_ds_path,
        flights_blob_path,
        tickets_blob_path,
        seats_blob_path,
        load_all_data=False,
    ) -> tuple[
        List[models.Airport],
        List[models.Amenity],
        List[models.Policy],
        CSVStreamer[models.Flight],
        CSVStreamer[models.Ticket],
        CSVStreamer[models.Seat],
    ]:
        storage_client = StorageClient.create_anonymous_client()
        bucket = storage_client.bucket(bucket_path)

        airports: List[models.Airport] = []
        with open(airports_ds_path, "r") as f:
            reader = csv.DictReader(f, delimiter=",")
            airports = [models.Airport.model_validate(line) for line in reader]

        amenities: list[models.Amenity] = []
        with open(amenities_ds_path, "r") as f:
            reader = csv.DictReader(f, delimiter=",")
            amenities = [models.Amenity.model_validate(line) for line in reader]

        policies: List[models.Policy] = []
        with open(policies_ds_path, "r") as f:
            reader = csv.DictReader(f, delimiter=",")
            policies = [models.Policy.model_validate(line) for line in reader]

        flights_streamer = CSVStreamer[models.Flight](
            bucket,
            flights_blob_path,
            None if load_all_data else 70000,
            models.Flight.model_validate,
        )
        ticket_streamer = CSVStreamer[models.Ticket](
            bucket,
            tickets_blob_path,
            None if load_all_data else 1000,
            models.Ticket.model_validate,
        )
        seats_streamer = CSVStreamer[models.Seat](
            bucket,
            seats_blob_path,
            None if load_all_data else 1000,
            models.Seat.model_validate,
        )

        return (
            airports,
            amenities,
            policies,
            flights_streamer,
            ticket_streamer,
            seats_streamer,
        )

    async def export_dataset(
        self,
        airports,
        amenities,
        policies,
        flights,
        tickets,
        seats,
        airports_new_path,
        amenities_new_path,
        policies_new_path,
        flights_new_path,
        tickets_new_path,
        seats_new_path,
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
                "id",
                "content",
                "embedding",
            ]
            writer = csv.DictWriter(f, col_names, delimiter=",")
            writer.writeheader()
            for p in policies:
                writer.writerow(p.model_dump())

        with open(tickets_new_path, "w") as t:
            col_names = [
                "id",
                "user_id",
                "user_name",
                "user_email",
                "airline",
                "flight_number",
                "departure_airport",
                "arrival_airport",
                "departure_time",
                "arrival_time",
                "seat_row",
                "seat_letter",
            ]
            writer = csv.DictWriter(t, col_names, delimiter=",")
            writer.writeheader()
            for ti in tickets:
                writer.writerow(ti.model_dump())

        with open(seats_new_path, "w") as s:
            col_names = [
                "flight_id",
                "seat_row",
                "seat_letter",
                "seat_type",
                "seat_class",
                "is_reserved",
                "ticket_id",
            ]
            writer = csv.DictWriter(s, col_names, delimiter=",")
            writer.writeheader()
            for se in seats:
                writer.writerow(se.model_dump())

    @abstractmethod
    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        policies: list[models.Policy],
        flights_streamer: CSVStreamer[models.Flight],
        tickets_streamer: CSVStreamer[models.Ticket],
        seats_streamer: CSVStreamer[models.Seat],
        stream_limit: int = 10000,
    ) -> None:
        pass

    @abstractmethod
    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Policy],
        list[models.Flight],
        list[models.Ticket],
        list[models.Seat],
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
        self,
        query: str,
        query_embedding: list[float],
        similarity_threshold: float,
        top_k: int,
        ufl: UIFriendlyLogger,
        open_time: Optional[str],
        open_day: Optional[str],
    ) -> list[Any]:
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
    async def search_flight_seats(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
        seat_row: int | None,
        seat_letter: str | None,
        seat_class: str | None,
        seat_type: str | None,
    ) -> list[models.Seat]:
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
        ufl: UIFriendlyLogger,
        seat_row: int | None = None,
        seat_letter: str | None = None,
    ):
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def list_tickets(
        self,
        user_id: str,
    ) -> list[models.Ticket]:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def policies_search(
        self,
        query: str,
        query_embedding: list[float],
        similarity_threshold: float,
        top_k: int,
        ufl: UIFriendlyLogger,
    ) -> list[str]:
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
