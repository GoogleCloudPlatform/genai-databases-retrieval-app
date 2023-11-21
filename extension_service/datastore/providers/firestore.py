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
from datetime import datetime, timedelta
from typing import Literal, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference
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
        async def delete_collections(collection_list: list[AsyncCollectionReference]):
            # Checks if colelction exists and deletes all documents
            delete_tasks = []
            for collection_ref in collection_list:
                collection_exists = collection_ref.limit(1).stream()
                if not collection_exists:
                    continue

                docs = collection_ref.stream()
                async for doc in docs:
                    delete_tasks.append(asyncio.create_task(doc.reference.delete()))
            asyncio.gather(*delete_tasks)

        # Check if the collections already exist; if so, delete collections
        airports_ref = self.__client.collection("airports")
        amenities_ref = self.__client.collection("amenities")
        flights_ref = self.__client.collection("flights")
        await delete_collections([airports_ref, amenities_ref, flights_ref])

        # initialize collections
        create_airports_tasks = []
        for airport in airports:
            create_airports_tasks.append(
                self.__client.collection("airports")
                .document(str(airport.id))
                .set(
                    {
                        "iata": airport.iata,
                        "name": airport.name,
                        "city": airport.city,
                        "country": airport.country,
                    }
                )
            )
        await asyncio.gather(*create_airports_tasks)
        create_amenities_tasks = []
        for amenity in amenities:
            create_amenities_tasks.append(
                self.__client.collection("amenities")
                .document(str(amenity.id))
                .set(
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
            )
        await asyncio.gather(*create_amenities_tasks)
        create_flights_tasks = []
        for flight in flights:
            create_flights_tasks.append(
                self.__client.collection("flights")
                .document(str(flight.id))
                .set(
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
            )
            if len(create_flights_tasks) % 10000 == 0:
                # avoid gRPC batch write timeout error
                await asyncio.gather(*create_flights_tasks)
                create_flights_tasks.clear()
        await asyncio.gather(*create_flights_tasks)

    async def export_data(
        self,
    ) -> tuple[list[models.Airport], list[models.Amenity], list[models.Flight]]:
        airport_docs = self.__client.collection("airports").stream()
        amenities_docs = self.__client.collection("amenities").stream()
        flights_docs = self.__client.collection("flights").stream()

        airports = []

        async for doc in airport_docs:
            airport_dict = doc.to_dict()
            airport_dict["id"] = doc.id
            airports.append(models.Airport.model_validate(airport_dict))

        amenities = []
        async for doc in amenities_docs:
            amenity_dict = doc.to_dict()
            amenity_dict["id"] = doc.id
            amenities.append(models.Amenity.model_validate(amenity_dict))

        flights = []
        async for doc in flights_docs:
            flight_dict = doc.to_dict()
            flight_dict["id"] = doc.id
            flights.append(models.Flight.model_validate(flight_dict))

        return airports, amenities, flights

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        query = self.__client.collection("airports").where(
            filter=FieldFilter("id", "==", id)
        )
        airport_doc = await query.get()
        airport_dict = airport_doc.to_dict() | {"id": airport_doc.id}
        return models.Airport.model_validate(airport_dict)

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        query = self.__client.collection("airports").where(
            filter=FieldFilter("iata", "==", iata)
        )
        airport_doc = await query.get()
        airport_dict = airport_doc.to_dict() | {"id": airport_doc.id}
        return models.Airport.model_validate(airport_dict)

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

        docs = query.stream()
        airports = []
        async for doc in docs:
            airport_dict = doc.to_dict() | {"id": doc.id}
            airports.append(models.Airport.model_validate(airport_dict))
        return airports

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        query = self.__client.collection("amenities").where(
            filter=FieldFilter("id", "==", id)
        )
        amenity_doc = await query.get()
        amenity_dict = amenity_doc.to_dict() | {"id": amenity_doc.id}
        return models.Amenity.model_validate(amenity_dict)

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[models.Amenity]:
        raise NotImplementedError("Semantic search not yet supported in Firestore.")

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        query = self.__client.collection("flights").where(
            filter=FieldFilter("id", "==", flight_id)
        )
        flight_doc = await query.get()
        flight_dict = flight_doc.to_dict() | {"id": flight_doc.id}
        return models.Flight.model_validate(flight_dict)

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

        docs = query.stream()
        flights = []
        async for doc in docs:
            flight_dict = doc.to_dict() | {"id": doc.id}
            flights.append(models.Airport.model_validate(flight_dict))
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

        docs = query.stream()
        flights = []
        async for doc in docs:
            flight_dict = doc.to_dict() | {"id": doc.id}
            flights.append(models.Airport.model_validate(flight_dict))
        return flights

    async def close(self):
        self.__client.close()
