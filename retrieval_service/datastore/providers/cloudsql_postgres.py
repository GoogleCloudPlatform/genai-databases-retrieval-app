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
from sqlalchemy import text
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

    def __init__(self, pool: AsyncEngine):
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
        tickets: list[models.Ticket],
        seats: list[models.Seat],
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
            await conn.commit()

            # If the table already exists, drop it to avoid conflicts
            await conn.execute(text("DROP TABLE IF EXISTS tickets CASCADE"))
            # Create a new table
            await conn.execute(
                text(
                    """
                    CREATE TABLE tickets(
                        id INTEGER PRIMARY KEY,
                        user_id TEXT,
                        user_name TEXT,
                        user_email TEXT,
                        airline TEXT,
                        flight_number TEXT,
                        departure_airport TEXT,
                        arrival_airport TEXT,
                        departure_time TIMESTAMP,
                        arrival_time TIMESTAMP,
                        seat_row INTEGER,
                        seat_letter TEXT
                    )
                    """
                )
            )
            # Insert all the data
            await conn.execute(
                text(
                    """
                    INSERT INTO tickets VALUES (:id, :user_id, :user_name,
                      :user_email, :airline, :flight_number,
                      :departure_airport, :arrival_airport, :departure_time,
                      :arrival_time, :seat_row, :seat_letter)
                    """
                ),
                [
                    {
                        "id": t.id,
                        "user_id": t.user_id,
                        "user_name": t.user_name,
                        "user_email": t.user_email,
                        "airline": t.airline,
                        "flight_number": t.flight_number,
                        "departure_airport": t.departure_airport,
                        "arrival_airport": t.arrival_airport,
                        "departure_time": t.departure_time,
                        "arrival_time": t.arrival_time,
                        "seat_row": t.seat_row,
                        "seat_letter": t.seat_letter,
                    }
                    for t in tickets
                ],
            )
            await conn.commit()

            # If the table already exists, drop it to avoid conflicts
            await conn.execute(text("DROP TABLE IF EXISTS seats CASCADE"))
            # Create a new table
            await conn.execute(
                text(
                    """
                    CREATE TABLE seats(
                        flight_id INTEGER,
                        seat_row INTEGER,
                        seat_letter TEXT,
                        seat_type TEXT,
                        seat_class TEXT,
                        is_reserved BOOL,
                        ticket_id INTEGER
                    )
                    """
                )
            )
            # Insert all the data
            await conn.execute(
                text(
                    """
                    INSERT INTO seats VALUES (:flight_id, :seat_row, :seat_letter,
                      :seat_type, :seat_class, :is_reserved, :ticket_id)
                    """
                ),
                [
                    {
                        "flight_id": s.flight_id,
                        "seat_row": s.seat_row,
                        "seat_letter": s.seat_letter,
                        "seat_type": s.seat_type,
                        "seat_class": s.seat_class,
                        "is_reserved": s.is_reserved,
                        "ticket_id": s.ticket_id,
                    }
                    for s in seats
                ],
            )
            await conn.commit()

    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Ticket],
        list[models.Seat],
    ]:
        async with self.__pool.connect() as conn1, self.__pool.connect() as conn2, self.__pool.connect() as conn3, self.__pool.connect() as conn4, self.__pool.connect() as conn5:
            airport_task = asyncio.create_task(
                conn1.execute(text("""SELECT * FROM airports"""))
            )
            amenity_task = asyncio.create_task(
                conn2.execute(text("""SELECT * FROM amenities"""))
            )
            flights_task = asyncio.create_task(
                conn3.execute(text("""SELECT * FROM flights"""))
            )
            tickets_task = asyncio.create_task(
                conn4.execute(text("""SELECT * FROM tickets LIMIT 1000"""))
            )
            seats_task = asyncio.create_task(
                conn5.execute(text("""SELECT * FROM seats LIMIT 1000"""))
            )

            airport_results = (await airport_task).mappings().fetchall()
            amenity_results = (await amenity_task).mappings().fetchall()
            flights_results = (await flights_task).mappings().fetchall()
            tickets_results = (await tickets_task).mappings().fetchall()
            seats_results = (await seats_task).mappings().fetchall()

            airports = [models.Airport.model_validate(a) for a in airport_results]
            amenities = [models.Amenity.model_validate(a) for a in amenity_results]
            flights = [models.Flight.model_validate(f) for f in flights_results]
            tickets = [models.Ticket.model_validate(t) for t in tickets_results]
            seats = [models.Seat.model_validate(s) for s in seats_results]
            return airports, amenities, flights, tickets, seats

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
    ) -> list[models.Amenity]:
        async with self.__pool.connect() as conn:
            s = text(
                """
                SELECT id, name, description, location, terminal, category, hour
                  FROM (
                      SELECT id, name, description, location, terminal, category, hour,
                        1 - (embedding <=> :query_embedding) AS similarity
                      FROM amenities
                      WHERE 1 - (embedding <=> :query_embedding) > :similarity_threshold
                      ORDER BY similarity DESC
                      LIMIT :top_k
                  ) AS sorted_amenities
                """
            )
            params = {
                "query_embedding": query_embedding,
                "similarity_threshold": similarity_threshold,
                "top_k": top_k,
            }
            results = (await conn.execute(s, params)).mappings().fetchall()

        res = [models.Amenity.model_validate(r) for r in results]
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
        seat_row: int | None = None,
        seat_letter: str | None = None,
    ):
        raise NotImplementedError("Not Implemented")

    async def search_flight_seats(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
        seat_row: str | None,
        seat_letter: str | None,
        seat_class: str | None,
        seat_type: str | None,
    ) -> list[models.Seat]:
        raise NotImplementedError("Not Implemented")

    async def list_tickets(
        self,
        user_id: str,
    ) -> list[models.Ticket]:
        raise NotImplementedError("Not Implemented")

    async def close(self):
        await self.__pool.dispose()
