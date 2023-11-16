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

from datetime import datetime, timedelta
from typing import Literal, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel

import models

from .. import datastore


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["firestore"]
    projectId: Optional[str]


class Client(datastore.Client[Config]):
    __client: firestore.AsyncClient

    @datastore.classproperty
    def kind(cls):
        return "firestore"

    def __init__(self, client: firestore.AsyncClient):
        self.__client = client

    @classmethod
    async def create(cls, config: Config) -> "Client":
        return cls(firestore.AsyncClient(project=config.projectId))

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
    ) -> None:
        async def delete_collection(coll_ref, batch_size=400):
            # Deletes all documents within a collection in batches.
            # Prevents out-of-memory error in case the collection is large.
            docs = await coll_ref.limit(batch_size).stream()
            deleted = 0

            async for doc in docs:
                await doc.reference.delete()
                deleted = deleted + 1

            if deleted >= batch_size:
                return await delete_collection(coll_ref, batch_size)

        # Check if the collections already exist; if so, delete collections
        airports_ref = self.__client.collection("airports")
        airports_exist = await airports_ref.limit(1).get()
        if airports_exist:
            await delete_collection(airports_ref)

        amenities_ref = self.__client.collection("amenities")
        amenities_exist = await amenities_ref.limit(1).get()
        if amenities_exist:
            await delete_collection(amenities_ref)

        flights_ref = self.__client.collection("flights")
        flights_exist = await flights_ref.limit(1).get()
        if flights_exist:
            await delete_collection(flights_ref)

        # initialize collections
        for airport in airports:
            await self.__client.collection("airports").document(str(airport.id)).set(
                {
                    "iata": airport.iata,
                    "name": airport.name,
                    "city": airport.city,
                    "country": airport.country,
                }
            )
        for amenity in amenities:
            await self.__client.collection("amenities").document(str(amenity.id)).set(
                {
                    "name": amenity.name,
                    "description": amenity.description,
                    "location": amenity.location,
                    "terminal": amenity.terminal,
                    "category": amenity.category,
                    "hour": amenity.hour,
                    "content": amenity.content,
                    "embedding": amenity.embedding,
                }
            )
        for flight in flights:
            await self.__client.collection("flights").document(str(flight.id)).set(
                {
                    "airline": flight.airline,
                    "flight_number": flight.flight_number,
                    "departure_airport": flight.departure_airport,
                    "arrival_airport": flight.arrival_airport,
                    "departure_time": flight.departure_time,
                    "arrival_time": flight.arrival_time,
                    "departure_gate": flight.departure_gate,
                    "arrival_gate": flight.arrival_gate,
                }
            )

    async def export_data(
        self,
    ) -> tuple[list[models.Airport], list[models.Amenity], list[models.Flight]]:
        airport_docs = self.__client.collection("airports").stream()
        amenities_docs = self.__client.collection("amenities").stream()
        flights_docs = self.__client.collection("flights").stream()

        airports = []

        for doc in airport_docs:
            airport_dict = doc.to_dict()
            airport_dict["id"] = doc.id
            airports.append(models.Airport.model_validate(airport_dict))

        amenities = []
        for doc in amenities_docs:
            amenity_dict = doc.to_dict()
            amenity_dict["id"] = doc.id
            amenities.append(models.Amenity.model_validate(amenity_dict))

        flights = []
        for doc in flights_docs:
            flight_dict = doc.to_dict()
            flight_dict["id"] = doc.id
            flights.append(models.Flight.model_validate(flight_dict))

        return airports, amenities, flights

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        query = self.__client.collection("airports").where(
            filter=FieldFilter("id", "==", id)
        )
        return models.Airport.model_validate(query.stream().to_dict())

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        query = self.__client.collection("airports").where(
            filter=FieldFilter("iata", "==", iata)
        )
        return models.Airport.model_validate(await query.stream().to_dict())

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        query = self.__client.collection("airports")

        if country is not None:
            query = query.where("country", "==", country)

        if city is not None:
            query = query.where("city", "==", city)

        if name is not None:
            query = query.where("name", ">=", name).where("name", "<=", name + "\uf8ff")

        docs = await query.stream()

        airports = [models.Airport.model_validate(dict(doc)) for doc in docs]
        return airports

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
        return models.Amenity.model_validate(await query.stream().to_dict())

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[models.Amenity]:
        query = (
            self.__client.collection("amenities")
            .where("embedding", ">", 1 - similarity_threshold)
            .select(
                "id", "name", "description", "location", "terminal", "category", "hour"
            )
            .order_by("similarity", direction="descending")
            .limit(top_k)
        )

        docs = await query.stream()

        amenities = [models.Amenity.model_validate(dict(doc)) for doc in docs]
        return amenities

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        query = self.__client.collection("flights").where(
            filter=FieldFilter("id", "==", id)
        )
        return models.Flight.model_validate(await query.stream().to_dict())

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> list[models.Flight]:
        query = (
            self.__client.collection("flights")
            .where(filter=FieldFilter("airline", "==", airline))
            .where(filter=FieldFilter("flight_number", "==", number))
        )

        docs = await query.stream()

        flights = [models.Flight.model_validate(dict(doc)) for doc in docs]
        return flights

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        date_timestamp = datetime.combine(date_obj, datetime.min.time())
        query = (
            self.__client.collection("flights")
            .where("departure_time", ">=", date_timestamp - timedelta(days=1))
            .where("departure_time", "<=", date_timestamp + timedelta(days=1))
        )

        if departure_airport is None:
            query = query.where("departure_airport", "==", departure_airport)
        if arrival_airport is None:
            query = query.where("arrival_airport", "==", arrival_airport)

        docs = await query.stream()

        flights = [models.Flight.model_validate(dict(doc)) for doc in docs]
        return flights

    async def close(self):
        self.__client.close()
