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
from typing import Any, Literal, Optional

import asyncpg
from google.cloud.sql.connector import Connector, RefreshStrategy
from pgvector.asyncpg import register_vector
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import models

from .. import datastore
from .postgres_datastore import PostgresDatastore

CLOUD_SQL_PG_IDENTIFIER = "cloudsql-postgres"


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["cloudsql-postgres"]
    project: str
    region: str
    instance: str
    user: str
    password: str
    database: str


class Client(datastore.Client[Config]):
    __pg_ds: PostgresDatastore
    __connector: Optional[Connector] = None

    @datastore.classproperty
    def kind(cls):
        return CLOUD_SQL_PG_IDENTIFIER

    def __init__(self, pool: AsyncEngine):
        self.__pg_ds = PostgresDatastore(pool)

    @classmethod
    async def create(cls, config: Config) -> "Client":
        async def getconn() -> asyncpg.Connection:
            if cls.__connector is None:
                loop = asyncio.get_running_loop()
                cls.__connector = Connector(
                    loop=loop, refresh_strategy=RefreshStrategy.LAZY
                )

            conn: asyncpg.Connection = await cls.__connector.connect_async(
                # Cloud SQL instance connection name
                f"{config.project}:{config.region}:{config.instance}",
                "asyncpg",
                user=f"{config.user}",
                password=f"{config.password}",
                db=f"{config.database}",
            )
            await register_vector(conn)
            return conn

        pool = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=getconn,
        )
        if pool is None:
            raise TypeError("pool not instantiated")
        return cls(pool)

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        await self.__pg_ds.initialize_data(airports, amenities, flights, policies)

    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        return await self.__pg_ds.export_data()

    async def get_airport_by_id(
        self, id: int
    ) -> tuple[Optional[models.Airport], Optional[str]]:
        return await self.__pg_ds.get_airport_by_id(id)

    async def get_airport_by_iata(
        self, iata: str
    ) -> tuple[Optional[models.Airport], Optional[str]]:
        return await self.__pg_ds.get_airport_by_iata(iata)

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> tuple[list[models.Airport], Optional[str]]:
        return await self.__pg_ds.search_airports(country, city, name)

    async def get_amenity(
        self, id: int
    ) -> tuple[Optional[models.Amenity], Optional[str]]:
        return await self.__pg_ds.get_amenity(id)

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> tuple[list[Any], Optional[str]]:
        return await self.__pg_ds.amenities_search(
            query_embedding, similarity_threshold, top_k
        )

    async def get_flight(
        self, flight_id: int
    ) -> tuple[Optional[models.Flight], Optional[str]]:
        return await self.__pg_ds.get_flight(flight_id)

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> tuple[list[models.Flight], Optional[str]]:
        return await self.__pg_ds.search_flights_by_number(airline, number)

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> tuple[list[models.Flight], Optional[str]]:
        return await self.__pg_ds.search_flights_by_airports(
            date, departure_airport, arrival_airport
        )

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
    ) -> tuple[Optional[models.Flight], Optional[str]]:
        return await self.__pg_ds.validate_ticket(
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
        await self.__pg_ds.insert_ticket(
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
        return await self.__pg_ds.list_tickets(user_id)

    async def policies_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> tuple[list[str], Optional[str]]:
        return await self.__pg_ds.policies_search(
            query_embedding, similarity_threshold, top_k
        )

    async def close(self):
        await self.__pg_ds.close()
