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

from pydantic import BaseModel
from neo4j import GraphDatabase

from typing import List, Literal, Optional

from .. import datastore

import models

NEO4J_IDENTIFIER = "neo4j"


class AuthConfig(BaseModel):
    username: str
    password: str


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["neo4j"]
    uri: str
    auth: AuthConfig


class SimpleAmenity(BaseModel):
    name: str
    description: str
    category: str


class Client(datastore.Client[Config]):
    __driver: GraphDatabase.driver

    @datastore.classproperty
    def kind(cls):
        return NEO4J_IDENTIFIER

    def __init__(self, driver):
        self.__driver = driver

    @classmethod
    async def create(cls, config: Config) -> "Client":
        return cls(
            GraphDatabase.driver(
                config.uri, auth=(config.auth.username, config.auth.password)
            )
        )

    async def initialize_data(
        self,
        airports: List[models.Airport],
        amenities: List[models.Amenity],
        flights: List[models.Flight],
        policies: List[models.Policy],
    ) -> None:
        def _initialize_graph(tx, amenities):
            for amenity in amenities:
                tx.run(
                    """
                    CREATE (a:Amenity {name: $name, description: $description, category: $category})
                """,
                    name=amenity.name,
                    description=amenity.description,
                    category=amenity.category,
                )

        with self.__driver.session() as session:
            session.write_transaction(_initialize_graph, amenities)

    async def export_data(self) -> List[SimpleAmenity]:
        def _get_all_amenities(tx):
            result = tx.run("MATCH (a:Amenity) RETURN a")
            return [record["a"] for record in result]

        with self.__driver.session() as session:
            amenity_results = session.read_transaction(_get_all_amenities)

        amenities = [SimpleAmenity(**a) for a in amenity_results]

        return amenities

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

    async def get_amenity(self, id: int) -> Optional[SimpleAmenity]:
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
        self.__driver.close()
