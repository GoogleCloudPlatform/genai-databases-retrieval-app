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
        airports: List[models.Airport],
        amenities: List[models.Amenity],
    ) -> None:
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
                  embedding vector(768)
                )
                """
            )
            # Insert all the data
            await conn.executemany(
                """INSERT INTO amenities VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                [
                    (
                        a.id,
                        a.name,
                        a.description,
                        a.location,
                        a.terminal,
                        a.category,
                        a.hour,
                        a.embedding,
                    )
                    for a in amenities
                ],
            )

    async def export_data(
        self,
    ) -> Tuple[List[models.Airport], List[models.Amenity]]:
        airport_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM airports""")
        )
        amenity_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM amenities""")
        )

        airports = [models.Airport.model_validate(dict(a)) for a in await airport_task]
        amenities = [models.Amenity.model_validate(dict(a)) for a in await amenity_task]

        return airports, amenities

    async def close(self):
        await self.__pool.close()
