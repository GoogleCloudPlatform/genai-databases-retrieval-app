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
from typing import Any, Dict, List, Literal, Tuple

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
        self, toys: List[models.Toy], airports: List[models.Airport], embeddings: List[models.Embedding]
    ) -> None:
        async with self.__pool.acquire() as conn:
            # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS products CASCADE")
            # Create a new table
            await conn.execute(
                """
                CREATE TABLE products(
                  product_id VARCHAR(1024) PRIMARY KEY,
                  product_name TEXT,
                  description TEXT,
                  list_price NUMERIC
                )
                """
            )
            # Insert all the data
            await conn.executemany(
                """INSERT INTO products VALUES ($1, $2, $3, $4)""",
                [
                    (t.product_id, t.product_name, t.description, t.list_price)
                    for t in toys
                ],
            )

            # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS airports CASCADE")
            # Create a new table
            await conn.execute(
                """
                CREATE TABLE airports(
                  airport_id VARCHAR(1024) PRIMARY KEY,
                  iata TEXT,
                  name TEXT,
                  city TEXT,
                  country TEXT
                )
                """
            )
            # Insert all the data
            await conn.executemany(
                """INSERT INTO products VALUES ($1, $2, $3, $4)""",
                [
                    (a.airport_id, a.iata, a.name, a.city, a.country)
                    for a in airports
                ],
            )

            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute("DROP TABLE IF EXISTS product_embeddings")
            await conn.execute(
                """
                CREATE TABLE product_embeddings(
                    product_id VARCHAR(1024) NOT NULL REFERENCES products(product_id),
                    content TEXT,
                    embedding vector(768))
                """
            )
            # Insert all the data
            await conn.executemany(
                """INSERT INTO product_embeddings VALUES ($1, $2, $3)""",
                [(e.product_id, e.content, e.embedding) for e in embeddings],
            )

    async def export_data(self) -> Tuple[List[models.Toy], List[models.Airport], List[models.Embedding]]:
        toy_task = asyncio.create_task(self.__pool.fetch("""SELECT * FROM products"""))
        airport_task = asyncio.create_task(self.__pool.fetch("""SELECT * FROM airports"""))
        emb_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM product_embeddings""")
        )

        toys = [models.Toy.model_validate(dict(t)) for t in await toy_task]
        airports = [models.Airport.model_validate(dict(a)) for a in await airport_task]
        embeddings = [models.Embedding.model_validate(dict(v)) for v in await emb_task]

        return toys, airports, embeddings

    async def semantic_similarity_search(
        self, query_embedding: List[float], similarity_threshold: float, top_k: int
    ) -> List[Dict[str, Any]]:
        results = await self.__pool.fetch(
            """
                WITH vector_matches AS (
                    SELECT product_id, 1 - (embedding <=> $1) AS similarity
                    FROM product_embeddings
                    WHERE 1 - (embedding <=> $1) > $2
                    ORDER BY similarity DESC
                    LIMIT $3
                )
                SELECT
                    product_name,
                    list_price,
                    description
                FROM products
                WHERE product_id IN (SELECT product_id FROM vector_matches)
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
