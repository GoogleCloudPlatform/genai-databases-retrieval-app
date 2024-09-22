# Copyright 2024 Google LLC
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

from typing import Any, Literal, Optional

import asyncpg
from google.cloud.alloydb.connector import AsyncConnector, RefreshStrategy
from pgvector.asyncpg import register_vector
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import models

from .. import datastore
from .postgres import Client as PostgresClient

ALLOYDB_PG_IDENTIFIER = "alloydb-postgres"


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["alloydb-postgres"]
    project: str
    region: str
    cluster: str
    instance: str
    user: str
    password: str
    database: str


class Client(datastore.Client[Config]):
    __connector: Optional[AsyncConnector] = None
    __pg_client: PostgresClient

    @datastore.classproperty
    def kind(cls):
        return ALLOYDB_PG_IDENTIFIER

    def __init__(self, async_engine: AsyncEngine):
        self.__pg_client = PostgresClient(async_engine)

    @classmethod
    async def create(cls, config: Config) -> "Client":
        async def getconn() -> asyncpg.Connection:
            if cls.__connector is None:
                cls.__connector = AsyncConnector(refresh_strategy=RefreshStrategy.LAZY)

            conn: asyncpg.Connection = await cls.__connector.connect(
                # Alloydb instance connection name
                f"projects/{config.project}/locations/{config.region}/clusters/{config.cluster}/instances/{config.instance}",
                "asyncpg",
                user=f"{config.user}",
                password=f"{config.password}",
                db=f"{config.database}",
                ip_type="PUBLIC",
            )
            await register_vector(conn)
            return conn

        async_engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=getconn,
        )
        if async_engine is None:
            raise TypeError("async_engine not instantiated")
        return cls(async_engine)

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        await self.__pg_client.initialize_data(airports, amenities, flights, policies)

    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        return await self.__pg_client.export_data()

    async def get_airport_by_id(
        self, id: int
    ) -> tuple[Optional[models.Airport], Optional[str]]:
        return await self.__pg_client.get_airport_by_id(id)

    async def get_airport_by_iata(
        self, iata: str
    ) -> tuple[Optional[models.Airport], Optional[str]]:
        return await self.__pg_client.get_airport_by_iata(iata)

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> tuple[list[models.Airport], Optional[str]]:
        return await self.__pg_client.search_airports(country, city, name)

    async def get_amenity(
        self, id: int
    ) -> tuple[Optional[models.Amenity], Optional[str]]:
        return await self.__pg_client.get_amenity(id)

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> tuple[list[Any], Optional[str]]:
        return await self.__pg_client.amenities_search(
            query_embedding, similarity_threshold, top_k
        )

    async def get_flight(
        self, flight_id: int
    ) -> tuple[Optional[models.Flight], Optional[str]]:
        return await self.__pg_client.get_flight(flight_id)

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> tuple[list[models.Flight], Optional[str]]:
        return await self.__pg_client.search_flights_by_number(airline, number)

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> tuple[list[models.Flight], Optional[str]]:
        return await self.__pg_client.search_flights_by_airports(
            date, departure_airport, arrival_airport
        )

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
    ) -> tuple[Optional[models.Flight], Optional[str]]:
        return await self.__pg_client.validate_ticket(
            airline, flight_number, departure_airport, departure_time
        )

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
        await self.__pg_client.insert_ticket(
            user_id,
            user_name,
            user_email,
            airline,
            flight_number,
            departure_airport,
            arrival_airport,
            departure_time,
            arrival_time,
        )

    async def list_tickets(
        self,
        user_id: str,
    ) -> tuple[list[Any], Optional[str]]:
        return await self.__pg_client.list_tickets(user_id)

    async def policies_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> tuple[list[str], Optional[str]]:
        return await self.__pg_client.policies_search(
            query_embedding, similarity_threshold, top_k
        )

    async def close(self):
        await self.__pg_client.close()
