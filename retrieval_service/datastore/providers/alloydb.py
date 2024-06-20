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

import asyncio
from datetime import datetime
from typing import Any, Literal, Optional

import asyncpg
from google.cloud.alloydb.connector import AsyncConnector
from pgvector.asyncpg import register_vector
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import models

from .. import datastore

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
    __pool: AsyncEngine

    @datastore.classproperty
    def kind(cls):
        return ALLOYDB_PG_IDENTIFIER

    def __init__(self, pool: AsyncEngine):
        self.__pool = pool

    @classmethod
    async def create(cls, config: Config) -> "Client":
        async def getconn() -> asyncpg.Connection:
            async with AsyncConnector() as connector:
                conn: asyncpg.Connection = await connector.connect(
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
        async with self.__pool.connect() as conn:
            # If the table already exists, drop it to avoid conflicts
            await conn.execute(text("DROP TABLE IF EXISTS airports CASCADE"))
            # Create a new table
            await conn.execute(
                text(
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
                text(
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

            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # If the table already exists, drop it to avoid conflicts
            await conn.execute(text("DROP TABLE IF EXISTS amenities CASCADE"))
            # Create a new table
            await conn.execute(
                text(
                    """
                    CREATE TABLE amenities(
                      id INT PRIMARY KEY,
                      name TEXT,
                      description TEXT,
                      location TEXT,
                      terminal TEXT,
                      category TEXT,
                      hour TEXT,
                      sunday_start_hour TIME,
                      sunday_end_hour TIME,
                      monday_start_hour TIME,
                      monday_end_hour TIME,
                      tuesday_start_hour TIME,
                      tuesday_end_hour TIME,
                      wednesday_start_hour TIME,
                      wednesday_end_hour TIME,
                      thursday_start_hour TIME,
                      thursday_end_hour TIME,
                      friday_start_hour TIME,
                      friday_end_hour TIME,
                      saturday_start_hour TIME,
                      saturday_end_hour TIME,
                      content TEXT NOT NULL,
                      embedding vector(768) NOT NULL
                    )
                    """
                )
            )
            # Insert all the data
            await conn.execute(
                text(
                    """
                    INSERT INTO amenities VALUES (:id, :name, :description, :location,
                      :terminal, :category, :hour, :sunday_start_hour, :sunday_end_hour,
                      :monday_start_hour, :monday_end_hour, :tuesday_start_hour,
                      :tuesday_end_hour, :wednesday_start_hour, :wednesday_end_hour,
                      :thursday_start_hour, :thursday_end_hour, :friday_start_hour,
                      :friday_end_hour, :saturday_start_hour, :saturday_end_hour, :content, :embedding)
                    """
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
                        "sunday_start_hour": a.sunday_start_hour,
                        "sunday_end_hour": a.sunday_end_hour,
                        "monday_start_hour": a.monday_start_hour,
                        "monday_end_hour": a.monday_end_hour,
                        "tuesday_start_hour": a.tuesday_start_hour,
                        "tuesday_end_hour": a.tuesday_end_hour,
                        "wednesday_start_hour": a.wednesday_start_hour,
                        "wednesday_end_hour": a.wednesday_end_hour,
                        "thursday_start_hour": a.thursday_start_hour,
                        "thursday_end_hour": a.thursday_end_hour,
                        "friday_start_hour": a.friday_start_hour,
                        "friday_end_hour": a.friday_end_hour,
                        "saturday_start_hour": a.saturday_start_hour,
                        "saturday_end_hour": a.saturday_end_hour,
                        "content": a.content,
                        "embedding": a.embedding,
                    }
                    for a in amenities
                ],
            )

            # If the table already exists, drop it to avoid conflicts
            await conn.execute(text("DROP TABLE IF EXISTS flights CASCADE"))
            # Create a new table
            await conn.execute(
                text(
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
                text(
                    """
                    INSERT INTO flights VALUES (:id, :airline, :flight_number,
                      :departure_airport, :arrival_airport, :departure_time,
                      :arrival_time, :departure_gate, :arrival_gate)
                    """
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

            # If the table already exists, drop it to avoid conflicts
            await conn.execute(text("DROP TABLE IF EXISTS tickets CASCADE"))
            # Create a new table
            await conn.execute(
                text(
                    """
                    CREATE TABLE tickets(
                        user_id TEXT,
                        user_name TEXT,
                        user_email TEXT,
                        airline TEXT,
                        flight_number TEXT,
                        departure_airport TEXT,
                        arrival_airport TEXT,
                        departure_time TIMESTAMP,
                        arrival_time TIMESTAMP
                    )
                    """
                )
            )

            # If the table already exists, drop it to avoid conflicts
            await conn.execute(text("DROP TABLE IF EXISTS policies CASCADE"))
            # Create a new table
            await conn.execute(
                text(
                    """
                    CREATE TABLE policies(
                      id INT PRIMARY KEY,
                      content TEXT NOT NULL,
                      embedding vector(768) NOT NULL
                    )
                    """
                )
            )
            # Insert all the data
            await conn.execute(
                text(
                    """
                    INSERT INTO policies VALUES (:id, :content, :embedding)
                    """
                ),
                [
                    {
                        "id": p.id,
                        "content": p.content,
                        "embedding": p.embedding,
                    }
                    for p in policies
                ],
            )
            await conn.commit()

    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        async with self.__pool.connect() as conn:
            airport_task = asyncio.create_task(
                conn.execute(text("""SELECT * FROM airports ORDER BY id ASC"""))
            )
            amenity_task = asyncio.create_task(
                conn.execute(text("""SELECT * FROM amenities ORDER BY id ASC"""))
            )
            flights_task = asyncio.create_task(
                conn.execute(text("""SELECT * FROM flights ORDER BY id ASC"""))
            )
            policy_task = asyncio.create_task(
                conn.execute(text("""SELECT * FROM policies ORDER BY id ASC"""))
            )

            airport_results = (await airport_task).mappings().fetchall()
            amenity_results = (await amenity_task).mappings().fetchall()
            flights_results = (await flights_task).mappings().fetchall()
            policy_results = (await policy_task).mappings().fetchall()

            airports = [models.Airport.model_validate(a) for a in airport_results]
            amenities = [models.Amenity.model_validate(a) for a in amenity_results]
            flights = [models.Flight.model_validate(f) for f in flights_results]
            policies = [models.Policy.model_validate(p) for p in policy_results]

            return airports, amenities, flights, policies

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        async with self.__pool.connect() as conn:
            s = text("""SELECT * FROM airports WHERE id=:id""")
            params = {"id": id}
            result = (await conn.execute(s, params)).mappings().fetchone()

        if result is None:
            return None

        res = models.Airport.model_validate(result)
        return res

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        async with self.__pool.connect() as conn:
            s = text("""SELECT * FROM airports WHERE iata ILIKE :iata""")
            params = {"iata": iata}
            result = (await conn.execute(s, params)).mappings().fetchone()

        if result is None:
            return None

        res = models.Airport.model_validate(result)
        return res

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                SELECT * FROM airports
                  WHERE (CAST(:country AS TEXT) IS NULL OR country ILIKE :country)
                  AND (CAST(:city AS TEXT) IS NULL OR city ILIKE :city)
                  AND (CAST(:name AS TEXT) IS NULL OR name ILIKE '%' || :name || '%')
                  LIMIT 10
                """
            )
            params = {
                "country": country,
                "city": city,
                "name": name,
            }
            results = (await conn.execute(s, params)).mappings().fetchall()

        res = [models.Airport.model_validate(r) for r in results]
        return res

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                SELECT id, name, description, location, terminal, category, hour
                FROM amenities WHERE id=:id
                """
            )
            params = {"id": id}
            result = (await conn.execute(s, params)).mappings().fetchone()

        if result is None:
            return None

        res = models.Amenity.model_validate(result)
        return res

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[Any]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                SELECT name, description, location, terminal, category, hour
                FROM amenities
                WHERE (embedding <=> :query_embedding) < :similarity_threshold
                ORDER BY (embedding <=> :query_embedding)
                LIMIT :top_k
                """
            )
            params = {
                "query_embedding": query_embedding,
                "similarity_threshold": similarity_threshold,
                "top_k": top_k,
            }
            results = (await conn.execute(s, params)).mappings().fetchall()

        res = [r for r in results]
        return res

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                SELECT * FROM flights
                  WHERE id = :flight_id
                """
            )
            params = {"flight_id": flight_id}
            result = (await conn.execute(s, params)).mappings().fetchone()

        if result is None:
            return None

        res = models.Flight.model_validate(result)
        return res

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> list[models.Flight]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                SELECT * FROM flights
                  WHERE airline = :airline
                  AND flight_number = :number
                  LIMIT 10
                """
            )
            params = {
                "airline": airline,
                "number": number,
            }
            results = (await conn.execute(s, params)).mappings().fetchall()

        res = [models.Flight.model_validate(r) for r in results]
        return res

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                SELECT * FROM flights
                  WHERE (CAST(:departure_airport AS TEXT) IS NULL OR departure_airport ILIKE :departure_airport)
                  AND (CAST(:arrival_airport AS TEXT) IS NULL OR arrival_airport ILIKE :arrival_airport)
                  AND departure_time >= CAST(:datetime AS timestamp)
                  AND departure_time < CAST(:datetime AS timestamp) + interval '1 day'
                  LIMIT 10
                """
            )
            params = {
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "datetime": datetime.strptime(date, "%Y-%m-%d"),
            }

            results = (await conn.execute(s, params)).mappings().fetchall()

        res = [models.Flight.model_validate(r) for r in results]
        return res

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
    ) -> Optional[models.Flight]:
        departure_time_datetime = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
        async with self.__pool.connect() as conn:
            s = text(
                """
                    SELECT * FROM flights
                    WHERE airline ILIKE :airline
                    AND flight_number ILIKE :flight_number
                    AND departure_airport ILIKE :departure_airport
                    AND departure_time = :departure_time
                """
            )
            params = {
                "airline": airline,
                "flight_number": flight_number,
                "departure_airport": departure_airport,
                "departure_time": departure_time_datetime,
            }
            result = (await conn.execute(s, params)).mappings().fetchone()

        if result is None:
            return None
        res = models.Flight.model_validate(result)
        return res

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
        departure_time_datetime = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
        arrival_time_datetime = datetime.strptime(arrival_time, "%Y-%m-%d %H:%M:%S")

        async with self.__pool.connect() as conn:
            s = text(
                """
                INSERT INTO tickets (
                    user_id,
                    user_name,
                    user_email,
                    airline,
                    flight_number,
                    departure_airport,
                    arrival_airport,
                    departure_time,
                    arrival_time
                ) VALUES (
                    :user_id,
                    :user_name,
                    :user_email,
                    :airline,
                    :flight_number,
                    :departure_airport,
                    :arrival_airport,
                    :departure_time,
                    :arrival_time
                );
            """
            )
            params = {
                "user_id": user_id,
                "user_name": user_name,
                "user_email": user_email,
                "airline": airline,
                "flight_number": flight_number,
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
            }
            results = (await conn.execute(s, params)).mappings().fetchall()
            if results != "INSERT 0 1":
                raise Exception("Ticket Insertion failure")

    async def list_tickets(
        self,
        user_id: str,
    ) -> list[models.Ticket]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                    SELECT * FROM tickets
                    WHERE user_id = :user_id
                """
            )
            params = {
                "user_id": user_id,
            }
            results = (await conn.execute(s, params)).mappings().fetchall()

        res = [models.Ticket.model_validate(r) for r in results]
        return res

    async def policies_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[str]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                SELECT content
                FROM policies
                WHERE (embedding <=> :query_embedding) < :similarity_threshold
                ORDER BY (embedding <=> :query_embedding)
                LIMIT :top_k
                """
            )
            params = {
                "query_embedding": query_embedding,
                "similarity_threshold": similarity_threshold,
                "top_k": top_k,
            }
            results = (await conn.execute(s, params)).mappings().fetchall()

        res = [r["content"] for r in results]
        return res

    async def close(self):
        await self.__pool.dispose()
