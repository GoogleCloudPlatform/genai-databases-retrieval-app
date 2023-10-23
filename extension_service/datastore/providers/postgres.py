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
from typing import Any, Dict, List, Literal

import asyncpg
from pgvector.asyncpg import register_vector
from pydantic import BaseModel

import models

from .. import datastore

POSTGRES_IDENTIFIER = "postgres"


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["postgres"]
    host: IPv4Address | IPv6Address = IPv4Address("127.0.0.1")
    port: int = 5432
    user: str
    password: str
    database: str


class Client(datastore.Client[Config]):
    __pool: asyncpg.Pool

    @datastore.classproperty
    def kind(cls):
        return "postgres"

    def __init__(self, pool: asyncpg.Pool):
        self.__pool = pool

    @classmethod
    async def create(cls, config: Config) -> "Client":
        async def init(conn):
            await register_vector(conn)

        pool = await asyncpg.create_pool(
            host=str(config.host),
            user=config.user,
            password=config.password,
            database=config.database,
            port=config.port,
            init=init,
        )
        if pool is None:
            raise TypeError("pool not instantiated")
        return cls(pool)

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: List[models.Flight],
    ) -> None:
        async with self.__pool.acquire() as conn:
            # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS flights CASCADE")
            # Create a new table
            await conn.execute(
                """
                CREATE TABLE flights(
                  id INTEGER PRIMARY KEY,
                  airline TEXT,
                  flight_number TEXT,
                  departure_airport TEXT,
                  arrival_airport TEXT,
                  departure_time TIMESTAMP,
                  arrival_time TIMESTAMP,
                  departure_gate TEXT,
                  arrival_gate TEXT
                )
                """
            )
            # Insert all the data
            await conn.executemany(
                """INSERT INTO flights VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                [
                    (
                        f.id,
                        f.airline,
                        f.flight_number,
                        f.departure_airport,
                        f.arrival_airport,
                        f.departure_time,
                        f.arrival_time,
                        f.departure_gate,
                        f.arrival_gate,
                    )
                    for f in flights
                ],
            )
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        async with self.__pool.acquire() as conn:
            # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS airports CASCADE")
            # Create a new table
            await conn.execute(
                """
                CREATE TABLE airports(
                  id INT PRIMARY KEY,
                  iata TEXT,
                  name TEXT,
                  city TEXT,
                  country TEXT
                )
                """
            )
            # Insert all the data
            await conn.executemany(
                """INSERT INTO airports VALUES ($1, $2, $3, $4, $5)""",
                [(a.id, a.iata, a.name, a.city, a.country) for a in airports],
            )

            # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS amenities CASCADE")
            # Create a new table
            await conn.execute(
                """
                CREATE TABLE amenities(
                  id INT PRIMARY KEY,
                  name TEXT,
                  description TEXT,
                  location TEXT,
                  terminal TEXT,
                  category TEXT,
                  hour TEXT,
                  content TEXT,
                  embedding vector(768)
                )
                """
            )
            # Insert all the data
            await conn.executemany(
                """INSERT INTO amenities VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                [
                    (
                        a.id,
                        a.name,
                        a.description,
                        a.location,
                        a.terminal,
                        a.category,
                        a.hour,
                        a.content,
                        a.embedding,
                    )
                    for a in amenities
                ],
            )

    async def export_data(
        self,
    ) -> tuple[list[models.Airport], list[models.Amenity], list[models.Flight]]:
        airport_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM airports""")
        )
        amenity_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM amenities""")
        )
        flights_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM flights""")
        )

        airports = [models.Airport.model_validate(dict(a)) for a in await airport_task]
        amenities = [models.Amenity.model_validate(dict(a)) for a in await amenity_task]
        flights = [models.Flight.model_validate(dict(f)) for f in await flights_task]
        return airports, amenities, flights

    async def get_amenity(self, id: int) -> list[Dict[str, Any]]:
        results = await self.__pool.fetch(
            """
                SELECT id, name, description, location, terminal, category, hour
                FROM amenities WHERE id=$1
            """,
            id,
        )

        results = [dict(r) for r in results]
        return results

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[Dict[str, Any]]:
        results = await self.__pool.fetch(
            """
                SELECT id, name, description, location, terminal, category, hour
                FROM (
                    SELECT id, name, description, location, terminal, category, hour, 1 - (embedding <=> $1) AS similarity
                    FROM amenities
                    WHERE 1 - (embedding <=> $1) > $2
                    ORDER BY similarity DESC
                    LIMIT $3
                ) AS sorted_amenities
            """,
            query_embedding,
            similarity_threshold,
            top_k,
            timeout=10,
        )
        results = [dict(r) for r in results]
        return results

    async def close(self):
        await self.__pool.close()
