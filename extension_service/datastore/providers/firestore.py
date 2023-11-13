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

import asyncio
from ipaddress import IPv4Address, IPv6Address
from typing import Any, Dict, Literal, Optional

import asyncpg
from pgvector.asyncpg import register_vector
from pydantic import BaseModel

import models

from .. import datastore

import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from firebase_admin import firestore_async
from google.cloud.firestore_v1.base_query import FieldFilter
import datetime


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["firestore"]
    projectId: str
    serviceAccountId: str


class Client(datastore.Client[Config]):
    __client: firestore.firestore

    @datastore.classproperty
    def kind(cls):
        return "firestore"

    def __init__(self, client: firestore.client):
        self.__client = client

    @classmethod
    async def create(cls, config: Config) -> "Client":
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(
            cred,
            options={
                "projectId": config.projectId,
                "serviceAccountId": config.serviceAccountId,
            },
        )
        return cls(firestore.client())

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
    ) -> None:
        for a in airports:
            self.__client.collection("airports").document(str(a.id)).set(
                {
                    "iata": a.iata,
                    "name": a.name,
                    "city": a.city,
                    "country": a.country,
                }
            )
        for a in amenities:
            self.__client.collection("amenities").document(str(a.id)).set(
                {
                    "name": a.name,
                    "description": a.description,
                    "location": a.location,
                    "terminal": a.terminal,
                    "category": a.category,
                    "hour": a.hour,
                    "content": a.content,
                    "embedding": a.embedding,
                }
            )
        for f in flights:
            self.__client.collection("flights").document(str(f.id)).set(
                {
                    "airline": f.airline,
                    "flight_number": f.flight_number,
                    "departure_airport": f.departure_airport,
                    "arrival_airport": f.arrival_airport,
                    "departure_time": f.departure_time,
                    "arrival_time": f.arrival_time,
                    "departure_gate": f.departure_gate,
                    "arrival_gate": f.arrival_gate,
                }
            )

    async def export_data(
        self,
    ) -> tuple[list[models.Airport], list[models.Amenity], list[models.Flight]]:
        airport_docs = self.__client.collection("airports").stream()
        amenities_docs = self.__client.collection("amenities").stream()
        flights_docs = self.__client.collection("flights").stream()

        airports = [
            models.Airport.model_validate(doc.to_dict()) for doc in await airport_docs
        ]
        amenities = [
            models.Amenity.model_validate(doc.to_dict()) for doc in await amenities_docs
        ]
        flights = [
            models.Flight.model_validate(doc.to_dict()) for doc in await flights_docs
        ]
        return airports, amenities, flights

    async def get_airport(self, id: int) -> Optional[models.Airport]:
        query = (
            self.__client.collection("airports")
            .where(filter=FieldFilter("id", "==", id))
            .select("id", "iata", "name", "city", "country")
        )
        return models.Airport.model_validate(query.get().to_dict())

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        query = (
            self.__client.collection("amenities")
            .where(filter=FieldFilter("id", "==", id))
            .select(
                "id",
                "name",
                "description",
                "location",
                "terminal",
                "category",
                "hour",
                "content",
                "embedding",
            )
        )
        return models.Airport.model_validate(query.get().to_dict())

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> Optional[list[models.Amenity]]:
        query = (
            self.__client.collection("amenities")
            .where("embedding", ">", 1 - similarity_threshold)
            .select(
                "id", "name", "description", "location", "terminal", "category", "hour"
            )
            .order_by("similarity", direction="descending")
            .limit(top_k)
        )

        docs = query.stream()
        if docs is []:
            return None

        amenities = [models.Amenity.model_validate(dict(doc)) async for doc in docs]
        return amenities

    async def get_flight(self, flight_id: int) -> Optional[list[models.Flight]]:
        query = self.__client.collection("flights").where(
            filter=FieldFilter("id", "==", id)
        )
        return models.Airport.model_validate(query.get().to_dict())

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> Optional[list[models.Flight]]:
        query = (
            self.__client.collection("flights")
            .where(filter=FieldFilter("airline", "==", airline))
            .where(filter=FieldFilter("flight_number", "==", flight_number))
        )

        docs = query.stream()
        if docs is []:
            return None

        flights = [models.Flight.model_validate(dict(doc)) async for doc in docs]
        return flights

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> Optional[list[models.Flight]]:
        # Check if either parameter is null.

        date_timestamp = datetime.combine(date, datetime.min.time())
        query = (
            self.__client.collection("flights")
            .where("departure_time", ">=", date_timestamp - datetime.timedelta(days=1))
            .where("departure_time", "<=", date_timestamp + datetime.timedelta(days=1))
        )

        if departure_airport is None:
            query = query.where("departure_airport", "==", departure_airport)
        if arrival_airport is None:
            query = query.where("arrival_airport", "==", arrival_airport)

    async def close(self):
        await self.__pool.close()
