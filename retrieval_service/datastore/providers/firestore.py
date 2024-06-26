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
from typing import Any, Literal, Optional

from google.cloud.firestore import AsyncClient  # type: ignore
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference
from google.cloud.firestore_v1.async_query import AsyncQuery
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
from pydantic import BaseModel

import models

from .. import datastore

FIRESTORE_IDENTIFIER = "firestore"


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["firestore"]
    projectId: Optional[str]


class Client(datastore.Client[Config]):
    __client: AsyncClient

    @datastore.classproperty
    def kind(cls):
        return FIRESTORE_IDENTIFIER

    def __init__(self, client: AsyncClient):
        self.__client = client
        self.__policies_collection = AsyncQuery(self.__client.collection("policies"))
        self.__amenities_collection = AsyncQuery(self.__client.collection("amenities"))

    @classmethod
    async def create(cls, config: Config) -> "Client":
        return cls(AsyncClient(project=config.projectId))

    async def __delete_collections(
        self, collection_list: list[AsyncCollectionReference]
    ):
        # Checks if collection exists and deletes all documents
        delete_tasks = []
        for collection_ref in collection_list:
            collection_exists = collection_ref.limit(1).stream()
            if not collection_exists:
                continue

            docs = collection_ref.stream()
            async for doc in docs:
                delete_tasks.append(asyncio.create_task(doc.reference.delete()))
        await asyncio.gather(*delete_tasks)

    async def parse_index_info(self, line: str) -> tuple[str, str]:
        # Extract collection and index-id from file path
        parts = line.split("/")
        collection_name = parts[-3]
        index_id = parts[-1]
        return collection_name, index_id

    async def __get_indices(self) -> dict[str, str]:
        list_vector_index_process = await asyncio.create_subprocess_exec(
            "gcloud",
            "alpha",
            "firestore",
            "indexes",
            "composite",
            "list",
            "--database=(default)",
            "--format=value(name)",  # prints name field
            stdout=asyncio.subprocess.PIPE,
        )

        # Capture output and ignore stderr
        stdout, __ = await list_vector_index_process.communicate()

        # Decode and format output
        index_lines = stdout.decode().strip().split("\n")

        indices = {}

        # Create a dict with collections and their corresponding vector index.
        for line in index_lines:
            if line:
                collection, index_id = await self.parse_index_info(line)
                indices[collection] = index_id

        return indices

    async def __delete_vector_index(self, indices: list[str]):
        # Check if the collection exists and deletes all indexes
        for index in indices:
            if index:
                delete_vector_index = await asyncio.create_subprocess_exec(
                    "gcloud",
                    "alpha",
                    "firestore",
                    "indexes",
                    "composite",
                    "delete",
                    index,
                    "--database=(default)",
                    "--quiet",  # Added to suppress delete warning
                )
                await delete_vector_index.wait()

    async def __create_vector_index(self, collection_name: str):
        create_vector_index = await asyncio.create_subprocess_exec(
            "gcloud",
            "alpha",
            "firestore",
            "indexes",
            "composite",
            "create",
            f"--collection-group={collection_name}",
            "--query-scope=COLLECTION",
            '--field-config=field-path=embedding,vector-config={"dimension":768,"flat":"{}"}',
            "--database=(default)",
        )
        await create_vector_index.wait()

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        # Check if the collections already exist; if so, delete collections
        airports_ref = self.__client.collection("airports")
        amenities_ref = self.__client.collection("amenities")
        flights_ref = self.__client.collection("flights")
        policies_ref = self.__client.collection("policies")
        await self.__delete_collections(
            [airports_ref, amenities_ref, flights_ref, policies_ref]
        )

        # Retrieve vector indexes and check if the collections already exist; if so, delete collections
        indices = await self.__get_indices()
        amenities_ref = indices.get("amenities", "")
        policies_ref = indices.get("policies", "")
        await self.__delete_vector_index([amenities_ref, policies_ref])

        # Initialize collections
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
                        # Firebase does not support datetime.time type
                        "sunday_start_hour": (
                            str(amenity.sunday_start_hour)
                            if amenity.sunday_start_hour
                            else None
                        ),
                        "sunday_end_hour": (
                            str(amenity.sunday_end_hour)
                            if amenity.sunday_end_hour
                            else None
                        ),
                        "monday_start_hour": (
                            str(amenity.monday_start_hour)
                            if amenity.monday_start_hour
                            else None
                        ),
                        "monday_end_hour": (
                            str(amenity.monday_end_hour)
                            if amenity.monday_end_hour
                            else None
                        ),
                        "tuesday_start_hour": (
                            str(amenity.tuesday_start_hour)
                            if amenity.tuesday_start_hour
                            else None
                        ),
                        "tuesday_end_hour": (
                            str(amenity.tuesday_end_hour)
                            if amenity.tuesday_end_hour
                            else None
                        ),
                        "wednesday_start_hour": (
                            str(amenity.wednesday_start_hour)
                            if amenity.wednesday_start_hour
                            else None
                        ),
                        "wednesday_end_hour": (
                            str(amenity.wednesday_end_hour)
                            if amenity.wednesday_end_hour
                            else None
                        ),
                        "thursday_start_hour": (
                            str(amenity.thursday_start_hour)
                            if amenity.thursday_start_hour
                            else None
                        ),
                        "thursday_end_hour": (
                            str(amenity.thursday_end_hour)
                            if amenity.thursday_end_hour
                            else None
                        ),
                        "friday_start_hour": (
                            str(amenity.friday_start_hour)
                            if amenity.friday_start_hour
                            else None
                        ),
                        "friday_end_hour": (
                            str(amenity.friday_end_hour)
                            if amenity.friday_end_hour
                            else None
                        ),
                        "saturday_start_hour": (
                            str(amenity.saturday_start_hour)
                            if amenity.saturday_start_hour
                            else None
                        ),
                        "saturday_end_hour": (
                            str(amenity.saturday_end_hour)
                            if amenity.saturday_end_hour
                            else None
                        ),
                        "content": amenity.content,
                        # Vector type does not support None value
                        "embedding": Vector(amenity.embedding or []),
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
                        "departure_time": flight.departure_time.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "arrival_time": flight.arrival_time.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
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
        create_policies_tasks = []
        for policy in policies:
            create_policies_tasks.append(
                self.__client.collection("policies")
                .document(str(policy.id))
                .set(
                    {
                        "content": policy.content,
                        # Vector type does not accept None value
                        "embedding": Vector(policy.embedding or []),
                    }
                )
            )
        await asyncio.gather(*create_policies_tasks)

        # Initialize single-field vector indexes
        await self.__create_vector_index("amenities")
        await self.__create_vector_index("policies")

    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        airport_docs = self.__client.collection("airports").stream()
        amenities_docs = self.__client.collection("amenities").stream()
        flights_docs = self.__client.collection("flights").stream()
        policies_docs = self.__client.collection("policies").stream()

        airports = []
        async for doc in airport_docs:
            airport_dict = doc.to_dict()
            airport_dict["id"] = doc.id
            airports.append(models.Airport.model_validate(airport_dict))

        amenities = []
        async for doc in amenities_docs:
            amenity_dict = doc.to_dict()
            amenity_dict["id"] = doc.id
            amenity_dict["embedding"] = list(amenity_dict["embedding"])
            amenities.append(models.Amenity.model_validate(amenity_dict))

        flights = []
        async for doc in flights_docs:
            flight_dict = doc.to_dict()
            flight_dict["id"] = doc.id
            flights.append(models.Flight.model_validate(flight_dict))

        policies = []
        async for doc in policies_docs:
            policy_dict = doc.to_dict()
            policy_dict["id"] = doc.id
            policy_dict["embedding"] = list(policy_dict["embedding"])
            policies.append(models.Policy.model_validate(policy_dict))

        return airports, amenities, flights, policies

    async def get_airport_by_id(
        self, id: int
    ) -> tuple[Optional[models.Airport], Optional[str]]:
        query = self.__client.collection("airports").where(
            filter=FieldFilter("id", "==", id)
        )
        airport_doc = await query.get()
        airport_dict = airport_doc.to_dict() | {"id": airport_doc.id}
        return models.Airport.model_validate(airport_dict), None

    async def get_airport_by_iata(
        self, iata: str
    ) -> tuple[Optional[models.Airport], Optional[str]]:
        query = self.__client.collection("airports").where(
            filter=FieldFilter("iata", "==", iata)
        )
        airport_doc = await query.get()
        airport_dict = airport_doc.to_dict() | {"id": airport_doc.id}
        return models.Airport.model_validate(airport_dict), None

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> tuple[list[models.Airport], Optional[str]]:
        query = self.__client.collection("airports")

        if country is not None:
            query = query.where("country", "==", country)

        if city is not None:
            query = query.where("city", "==", city)

        if name is not None:
            query = query.where("name", ">=", name).where("name", "<=", name + "\uf8ff")

        query = query.limit(10)

        docs = query.stream()
        airports = []
        async for doc in docs:
            airport_dict = doc.to_dict() | {"id": doc.id}
            airports.append(models.Airport.model_validate(airport_dict))
        return airports, None

    async def get_amenity(
        self, id: int
    ) -> tuple[Optional[models.Amenity], Optional[str]]:
        query = self.__client.collection("amenities").where(
            filter=FieldFilter("id", "==", id)
        )
        amenity_doc = await query.get()
        amenity_dict = amenity_doc.to_dict() | {"id": amenity_doc.id}
        amenity_dict["embedding"] = list(amenity_dict["embedding"])
        return models.Amenity.model_validate(amenity_dict)

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> tuple[list[Any], Optional[str]]:
        # Using the same similarity metric to the embedding model's training method
        # produce the most accurate result
        query = self.__amenities_collection.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_embedding),
            distance_measure=DistanceMeasure.DOT_PRODUCT,
            limit=top_k,
        )

        docs = query.stream()
        amenities = []
        async for doc in docs:
            amenity_dict = {
                "id": doc.id,
                "category": doc.get("category"),
                "description": doc.get("description"),
                "hour": doc.get("hour"),
                "location": doc.get("location"),
                "name": doc.get("name"),
                "terminal": doc.get("terminal"),
            }
            amenities.append(amenity_dict)
        return amenities, None

    async def get_flight(
        self, flight_id: int
    ) -> tuple[Optional[models.Flight], Optional[str]]:
        query = self.__client.collection("flights").where(
            filter=FieldFilter("id", "==", flight_id)
        )
        flight_doc = await query.get()
        flight_dict = flight_doc.to_dict() | {"id": flight_doc.id}
        return models.Flight.model_validate(flight_dict), None

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> tuple[list[models.Flight], Optional[str]]:
        query = (
            self.__client.collection("flights")
            .where(filter=FieldFilter("airline", "==", airline))
            .where(filter=FieldFilter("flight_number", "==", number))
            .limit(10)
        )

        docs = query.stream()
        flights = []
        async for doc in docs:
            flight_dict = doc.to_dict() | {"id": doc.id}
            flights.append(models.Flight.model_validate(flight_dict))
        return flights, None

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> tuple[list[models.Flight], Optional[str]]:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        date_timestamp = datetime.combine(date_obj, datetime.min.time())
        query = (
            self.__client.collection("flights")
            .where("departure_time", ">=", date_timestamp)
            .where("departure_time", "<", date_timestamp + timedelta(days=1))
            .limit(10)
        )

        if departure_airport is None:
            query = query.where("departure_airport", "==", departure_airport)
        if arrival_airport is None:
            query = query.where("arrival_airport", "==", arrival_airport)

        docs = query.stream()
        flights = []
        async for doc in docs:
            flight_dict = doc.to_dict() | {"id": doc.id}
            flights.append(models.Flight.model_validate(flight_dict))
        return flights, None

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
    ) -> tuple[Optional[models.Flight], Optional[str]]:
        raise NotImplementedError("Not Implemented")

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
        raise NotImplementedError("Not Implemented")

    async def list_tickets(
        self,
        user_id: str,
    ) -> tuple[list[models.Ticket], Optional[str]]:
        raise NotImplementedError("Not Implemented")

    async def policies_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> tuple[list[str], Optional[str]]:
        query = self.__policies_collection.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_embedding),
            distance_measure=DistanceMeasure.DOT_PRODUCT,
            limit=top_k,
        )

        policies = []
        async for doc in query.stream():
            policy_dict = {"id": doc.id, "content": doc.get("content")}
            policies.append(policy_dict)
        return policies, None

    async def close(self):
        self.__client.close()
