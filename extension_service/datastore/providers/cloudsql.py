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
from datetime import datetime
from typing import Any, Dict, Literal, Optional

import asyncpg
import sqlalchemy
from google.cloud.sql.connector import Connector
from pgvector.asyncpg import register_vector
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import models

from .. import datastore

POSTGRES_IDENTIFIER = "cloudsql-postgres"


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["cloudsql-postgres"]
    project: str
    region: str
    instance: str
    user: str
    password: str
    database: str


class Client(datastore.Client[Config]):
    __pool: AsyncEngine

    @datastore.classproperty
    def kind(cls):
        return "cloudsql-postgres"

    def __init__(self, pool: asyncpg.Pool):
        self.__pool = pool

    @classmethod
    async def create(cls, config: Config) -> "Client":
        loop = asyncio.get_running_loop()

        async def getconn() -> asyncpg.Connection:
            async with Connector(loop=loop) as connector:
                conn: asyncpg.Connection = await connector.connect_async(
                    # Cloud SQL instance connection name
                    f"{config.project}:{config.region}:{config.instance}",
                    "asyncpg",
                    user=f"{config.user}",
                    password=f"{config.password}",
                    db=f"{config.database}",
                )
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
    ) -> None:
        async with self.__pool.connect() as conn:
            # If the table already exists, drop it to avoid conflicts
            await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS airports CASCADE"))
            # Create a new table
            await conn.execute(
                sqlalchemy.text(
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
            )
            # Insert all the data
            await conn.execute(
                sqlalchemy.text(
                    """INSERT INTO airports VALUES (:id, :iata, :name, :city, :country)"""
                ),
                [
                    {
                        "id": a.id,
                        "iata": a.iata,
                        "name": a.name,
                        "city": a.city,
                        "country": a.country,
                    }
                    for a in airports
                ],
            )

            await conn.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector"))
            # If the table already exists, drop it to avoid conflicts
            await conn.execute(
                sqlalchemy.text("DROP TABLE IF EXISTS amenities CASCADE")
            )
            # Create a new table
            await conn.execute(
                sqlalchemy.text(
                    """
                    CREATE TABLE amenities(
                      id INT PRIMARY KEY,
                      name TEXT,
                      description TEXT,
                      location TEXT,
                      terminal TEXT,
                      category TEXT,
                      hour TEXT,
                      content TEXT NOT NULL,
                      embedding vector(768) NOT NULL
                    )
                    """
                )
            )
            # Insert all the data
            await conn.execute(
                sqlalchemy.text(
                    """INSERT INTO amenities VALUES (:id, :name, :description, :location, :terminal, :category, :hour, :content, :embedding)"""
                ),
                [
                    {
                        "id": a.id,
                        "name": a.name,
                        "description": a.description,
                        "location": a.location,
                        "terminal": a.terminal,
                        "category": a.category,
                        "hour": a.hour,
                        "content": a.content,
                        "embedding": "[" + ",".join(str(e) for e in a.embedding) + "]",
                    }
                    for a in amenities
                ],
            )

            # If the table already exists, drop it to avoid conflicts
            await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS flights CASCADE"))
            # Create a new table
            await conn.execute(
                sqlalchemy.text(
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
            )
            # Insert all the data
            await conn.execute(
                sqlalchemy.text(
                    """INSERT INTO flights VALUES (:id, :airline, :flight_number, :departure_airport, :arrival_airport, :departure_time, :arrival_time, :departure_gate, :arrival_gate)"""
                ),
                [
                    {
                        "id": f.id,
                        "airline": f.airline,
                        "flight_number": f.flight_number,
                        "departure_airport": f.departure_airport,
                        "arrival_airport": f.arrival_airport,
                        "departure_time": f.departure_time,
                        "arrival_time": f.arrival_time,
                        "departure_gate": f.departure_gate,
                        "arrival_gate": f.arrival_gate,
                    }
                    for f in flights
                ],
            )
            await conn.commit()

    async def export_data(
        self,
    ) -> tuple[list[models.Airport], list[models.Amenity], list[models.Flight]]:
        async with self.__pool.connect() as conn:
            airport_task = asyncio.create_task(
                conn.execute(sqlalchemy.text("""SELECT * FROM airports"""))
            )

            amenity_task = asyncio.create_task(
                conn.execute(sqlalchemy.text("""SELECT * FROM amenities"""))
            )
            flights_task = asyncio.create_task(
                conn.execute(sqlalchemy.text("""SELECT * FROM flights"""))
            )

            airport_results = (await airport_task).mappings().fetchall()
            amenity_results = (await amenity_task).mappings().fetchall()
            flights_results = (await flights_task).mappings().fetchall()

            airports = [models.Airport.model_validate(a) for a in airport_results]
            amenities = [models.Amenity.model_validate(a) for a in amenity_results]
            flights = [models.Flight.model_validate(f) for f in flights_results]
            return airports, amenities, flights

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        async with self.__pool.connect() as conn:
            result = await conn.execute(
                sqlalchemy.text(
                    """
                      SELECT * FROM airports WHERE id=:id
                    """
                ),
                parameters={
                    "id": id,
                },
            )
            result = result.mappings().fetchone()

        if result is None:
            return None

        result = models.Airport.model_validate(result)
        return result

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        async with self.__pool.connect() as conn:
            result = await conn.execute(
                sqlalchemy.text(
                    """
                      SELECT * FROM airports WHERE iata ILIKE :iata
                    """
                ),
                parameters={
                    "iata": iata,
                },
            )
            result = result.mappings().fetchone()

        if result is None:
            return None

        result = models.Airport.model_validate(result)
        return result

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        async with self.__pool.connect() as conn:
            results = await conn.execute(
                sqlalchemy.text(
                    """
                    SELECT * FROM airports
                    WHERE (CAST(:country AS TEXT) IS NULL OR country ILIKE :country)
                    AND (CAST(:city AS TEXT) IS NULL OR city ILIKE :city)
                    AND (CAST(:name AS TEXT) IS NULL OR name ILIKE '%' || :name || '%')
                    """
                ),
                parameters={
                    "country": country,
                    "city": city,
                    "name": name,
                },
            )
            results = results.mappings().fetchall()

        results = [models.Airport.model_validate(r) for r in results]
        return results

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        async with self.__pool.connect() as conn:
            result = await conn.execute(
                sqlalchemy.text(
                    """
                    SELECT id, name, description, location, terminal, category, hour
                    FROM amenities WHERE id=:id
                    """
                ),
                parameters={
                    "id": id,
                },
            )
            result = result.mappings().fetchone()

        if result is None:
            return None

        result = models.Amenity.model_validate(result)
        return result

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[models.Amenity]:
        async with self.__pool.connect() as conn:
            results = await conn.execute(
                sqlalchemy.text(
                    """
                        SELECT id, name, description, location, terminal, category, hour
                        FROM (
                            SELECT id, name, description, location, terminal, category, hour, 1 - (embedding <=> :query_embedding) AS similarity
                            FROM amenities
                            WHERE 1 - (embedding <=> :query_embedding) > :similarity_threshold
                            ORDER BY similarity DESC
                            LIMIT :top_k
                        ) AS sorted_amenities
                    """
                ),
                parameters={
                    "query_embedding": "["
                    + ",".join(str(e) for e in query_embedding)
                    + "]",
                    "similarity_threshold": similarity_threshold,
                    "top_k": top_k,
                },
            )
            results = results.mappings().fetchall()

        results = [models.Amenity.model_validate(r) for r in results]
        return results

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        async with self.__pool.connect() as conn:
            result = await conn.execute(
                sqlalchemy.text(
                    """
                        SELECT * FROM flights
                        WHERE id = :flight_id
                    """
                ),
                parameters={
                    "flight_id": flight_id,
                },
            )
            result = result.mappings().fetchone()

        if result is None:
            return None

        result = models.Flight.model_validate(result)
        return result

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> list[models.Flight]:
        async with self.__pool.connect() as conn:
            results = await conn.execute(
                sqlalchemy.text(
                    """
                        SELECT * FROM flights
                        WHERE airline = :airline
                        AND flight_number = :number;
                    """
                ),
                parameters={
                    "airline": airline,
                    "number": number,
                },
            )
            results = results.mappings().fetchall()
        results = [models.Flight.model_validate(dict(r)) for r in results]
        return results

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        # Check if either parameter is null.
        if departure_airport is None:
            departure_airport = "%"
        if arrival_airport is None:
            arrival_airport = "%"
        async with self.__pool.connect() as conn:
            results = await conn.execute(
                sqlalchemy.text(
                    """
                        SELECT * FROM flights
                        WHERE departure_airport LIKE :departure_airport
                        AND arrival_airport LIKE :arrival_airport
                        AND departure_time > CAST(:datetime AS timestamp) - interval '1 day'
                        AND departure_time < CAST(:datetime AS timestamp) + interval '1 day';
                    """
                ),
                parameters={
                    "departure_airport": departure_airport,
                    "arrival_airport": arrival_airport,
                    "datetime": datetime.strptime(date, "%Y-%m-%d"),
                },
            )
            results = results.mappings().fetchall()
        results = [models.Flight.model_validate(r) for r in results]
        return results

    async def close(self):
        await self.__pool.dispose()
