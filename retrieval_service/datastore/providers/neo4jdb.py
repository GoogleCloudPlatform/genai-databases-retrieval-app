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
from typing import Literal, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase
from pydantic import BaseModel

import models

from .. import datastore

NEO4J_IDENTIFIER = "neo4j"


class AuthConfig(BaseModel):
    username: str
    password: str


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["neo4j"]
    uri: str
    auth: AuthConfig

class Client(datastore.Client[Config]):
    __driver: AsyncDriver

    @datastore.classproperty
    def kind(cls):
        return NEO4J_IDENTIFIER

    def __init__(self, driver):
        self.__driver = driver

    @classmethod
    async def create(cls, config: Config) -> "Client":
        return cls(
            AsyncGraphDatabase.driver(
                config.uri, auth=(config.auth.username, config.auth.password)
            )
        )

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        async def delete_all(tx):
            await tx.run("MATCH (n) DETACH DELETE n")

        async def create_amenities(tx, amenities):
            for amenity in amenities:
                await tx.run(
                    """
                    CREATE (a:Amenity {id: $id, name: $name, description: $description, location: $location, terminal: $terminal, category: $category, hour: $hour})
                    """,
                    id=amenity.id,
                    name=amenity.name,
                    description=amenity.description,
                    location=amenity.location,
                    terminal=amenity.terminal,
                    category=amenity.category,
                    hour=amenity.hour,
                )

        async with self.__driver.session() as session:
            # Delete all exsiting nodes and relationships
            await session.execute_write(delete_all)

            await asyncio.gather(
                session.execute_write(create_amenities, amenities),
            )

    async def export_data(self) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        raise NotImplementedError("This client does not support airports.")

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        raise NotImplementedError("This client does not support airports.")

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        raise NotImplementedError("This client does not support airports.")

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        raise NotImplementedError("This client does not support airports.")

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        raise NotImplementedError("This client does not support amenities.")

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[dict]:
        raise NotImplementedError("This client does not support amenities.")

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        raise NotImplementedError("This client does not support flights.")

    async def search_flights_by_number(
        self, airline: str, flight_number: str
    ) -> list[models.Flight]:
        raise NotImplementedError("This client does not support flights.")

    async def search_flights_by_airports(
        self,
        date,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        raise NotImplementedError("This client does not support flights.")

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
    ) -> Optional[models.Flight]:
        raise NotImplementedError("This client does not support tickets.")

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
        raise NotImplementedError("This client does not support tickets.")

    async def list_tickets(self, user_id: str) -> list[models.Ticket]:
        raise NotImplementedError("This client does not support tickets.")

    async def policies_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[str]:
        raise NotImplementedError("This client does not support policies.")

    async def close(self):
        await self.__driver.close()
