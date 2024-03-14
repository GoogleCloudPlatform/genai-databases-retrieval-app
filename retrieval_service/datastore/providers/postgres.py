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
from ipaddress import IPv4Address, IPv6Address
from typing import Literal, Optional

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
        flights: list[models.Flight],
        tickets: list[models.Ticket],
        seats: list[models.Seat],
    ) -> None:
        async with self.__pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
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
            # Insert all the data
            await conn.executemany(
                """
                INSERT INTO amenities VALUES (
                  $1, $2, $3, $4, $5,
                  $6, $7, $8, $9, $10,
                  $11, $12, $13, $14, $15,
                  $16, $17, $18, $19, $20,
                  $21, $22, $23)
                """,
                [
                    (
                        a.id,
                        a.name,
                        a.description,
                        a.location,
                        a.terminal,
                        a.category,
                        a.hour,
                        a.sunday_start_hour,
                        a.sunday_end_hour,
                        a.monday_start_hour,
                        a.monday_end_hour,
                        a.tuesday_start_hour,
                        a.tuesday_end_hour,
                        a.wednesday_start_hour,
                        a.wednesday_end_hour,
                        a.thursday_start_hour,
                        a.thursday_end_hour,
                        a.friday_start_hour,
                        a.friday_end_hour,
                        a.saturday_start_hour,
                        a.saturday_end_hour,
                        a.content,
                        a.embedding,
                    )
                    for a in amenities
                ],
            )

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

            # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS tickets CASCADE")
            # Create a new table
            await conn.execute(
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
            # Insert all the data
            await conn.executemany(
                """INSERT INTO tickets VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
                [
                    (
                        t.id,
                        t.user_id,
                        t.user_name,
                        t.user_email,
                        t.airline,
                        t.flight_number,
                        t.departure_airport,
                        t.arrival_airport,
                        t.departure_time,
                        t.arrival_time,
                        t.seat_row,
                        t.seat_letter,
                    )
                    for t in tickets
                ],
            )

            # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS seats CASCADE")
            # Create a new table
            await conn.execute(
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
            # Insert all the data
            await conn.executemany(
                """INSERT INTO seats VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                [
                    (
                        s.flight_id,
                        s.seat_row,
                        s.seat_letter,
                        s.seat_type,
                        s.seat_class,
                        s.is_reserved,
                        None if s.ticket_id == -1 else s.ticket_id,
                    )
                    for s in seats
                ],
            )

    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Ticket],
        list[models.Seat],
    ]:
        airport_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM airports ORDER BY id ASC""")
        )
        amenity_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM amenities ORDER BY id ASC""")
        )
        flight_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM flights ORDER BY id ASC""")
        )
        tickets_task = asyncio.create_task(
            self.__pool.fetch("""SELECT * FROM tickets ORDER BY id ASC LIMIT 1000""")
        )
        seats_task = asyncio.create_task(
            self.__pool.fetch(
                """SELECT * FROM seats ORDER BY flight_id ASC LIMIT 1000"""
            )
        )

        airports = [models.Airport.model_validate(dict(a)) for a in await airport_task]
        amenities = [models.Amenity.model_validate(dict(a)) for a in await amenity_task]
        flights = [models.Flight.model_validate(dict(f)) for f in await flight_task]
        tickets = [models.Ticket.model_validate(dict(t)) for t in await tickets_task]
        seats = [models.Seat.model_validate(dict(s)) for s in await seats_task]
        return airports, amenities, flights, tickets, seats

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        result = await self.__pool.fetchrow(
            """
              SELECT * FROM airports WHERE id=$1
            """,
            id,
        )

        if result is None:
            return None

        result = models.Airport.model_validate(dict(result))
        return result

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        result = await self.__pool.fetchrow(
            """
              SELECT * FROM airports WHERE iata ILIKE $1
            """,
            iata,
        )

        if result is None:
            return None

        result = models.Airport.model_validate(dict(result))
        return result

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        results = await self.__pool.fetch(
            """
            SELECT * FROM airports
            WHERE ($1::TEXT IS NULL OR country ILIKE $1)
            AND ($2::TEXT IS NULL OR city ILIKE $2)
            AND ($3::TEXT IS NULL OR name ILIKE '%' || $3 || '%')
            """,
            country,
            city,
            name,
            timeout=10,
        )

        results = [models.Airport.model_validate(dict(r)) for r in results]
        return results

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        result = await self.__pool.fetchrow(
            """
            SELECT id, name, description, location, terminal, category, hour
            FROM amenities WHERE id=$1
            """,
            id,
        )

        if result is None:
            return None

        result = models.Amenity.model_validate(dict(result))
        return result

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[models.Amenity]:
        results = await self.__pool.fetch(
            """
            SELECT id, name, description, location, terminal, category, hour
            FROM (
                SELECT id, name, description, location, terminal, category,
                  hour, 1 - (embedding <=> $1) AS similarity
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

        results = [models.Amenity.model_validate(dict(r)) for r in results]
        return results

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        result = await self.__pool.fetchrow(
            """
                SELECT * FROM flights
                WHERE id = $1
            """,
            flight_id,
            timeout=10,
        )

        if result is None:
            return None

        result = models.Flight.model_validate(dict(result))
        return result

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> list[models.Flight]:
        results = await self.__pool.fetch(
            """
                SELECT * FROM flights
                WHERE airline = $1
                AND flight_number = $2;
            """,
            airline,
            number,
            timeout=10,
        )
        results = [models.Flight.model_validate(dict(r)) for r in results]
        return results

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
        departure_time_datetime = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
        results = await self.__pool.fetch(
            """
                SELECT
                  *
                FROM
                  seats
                WHERE
                  is_reserved = FALSE
                  AND flight_id = (
                  SELECT
                    id
                  FROM
                    flights
                  WHERE
                    airline = $1
                    AND flight_number = $2
                    AND departure_airport = $3
                    AND departure_time = $4::timestamp
                  LIMIT
                    1)
                  AND (CAST(seat_row AS VARCHAR) = $5 OR '' = $5)
                  AND (seat_letter = $6 OR '' = $6)
                  AND (seat_class = $7 OR '' = $7)
                  AND (seat_type = $8 OR '' = $8)
            """,
            airline,
            flight_number,
            departure_airport,
            departure_time_datetime,
            seat_row,
            seat_letter,
            seat_class,
            seat_type,
            timeout=10,
        )
        results = [models.Seat.model_validate(dict(r)) for r in results]
        return results

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        results = await self.__pool.fetch(
            """
                SELECT * FROM flights
                WHERE ($1::TEXT IS NULL OR departure_airport ILIKE $1)
                AND ($2::TEXT IS NULL OR arrival_airport ILIKE $2)
                AND departure_time >= $3::timestamp
                AND departure_time < $3::timestamp + interval '1 day';
            """,
            departure_airport,
            arrival_airport,
            datetime.strptime(date, "%Y-%m-%d"),
            timeout=10,
        )
        results = [models.Flight.model_validate(dict(r)) for r in results]
        return results

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        arrival_airport: str,
        departure_time: datetime,
        arrival_time: datetime,
    ) -> bool:
        results = await self.__pool.fetch(
            """
                SELECT * FROM flights
                WHERE airline ILIKE $1
                AND flight_number ILIKE $2
                AND departure_airport ILIKE $3
                AND arrival_airport ILIKE $4
                AND departure_time = $5::timestamp
                AND arrival_time = $6::timestamp;
            """,
            airline,
            flight_number,
            departure_airport,
            arrival_airport,
            departure_time,
            arrival_time,
            timeout=10,
        )
        if len(results) == 1:
            return True
        return False

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
        departure_time_datetime = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
        arrival_time_datetime = datetime.strptime(arrival_time, "%Y-%m-%d %H:%M:%S")
        if not await self.validate_ticket(
            airline,
            flight_number,
            departure_airport,
            arrival_airport,
            departure_time_datetime,
            arrival_time_datetime,
        ):
            raise Exception("Flight information not in database")
        async with self.__pool.acquire() as conn:
            async with conn.transaction():
                # If no seat is pre-selected, find the first seat on this flight
                if seat_row is None or seat_letter is None:
                    open_seat = await conn.fetchrow(
                        """
                            SELECT seat_row, seat_letter
                            FROM seats
                            WHERE flight_id = (
                                SELECT id
                                FROM flights
                                WHERE flight_number = $1 AND
                                        airline = $2 AND
                                        departure_airport = $3 AND
                                        departure_time = $4)
                                    AND is_reserved = FALSE;
                        """,
                        flight_number,
                        airline,
                        departure_airport,
                        departure_time_datetime,
                        timeout=10,
                    )
                    if not open_seat:
                        raise Exception("No seat on this flight.")
                    seat_row, seat_letter = (
                        open_seat["seat_row"],
                        open_seat["seat_letter"],
                    )
                # Book the ticket
                ticket_id = None
                ticket_booking_result = await conn.fetchrow(
                    """
                        INSERT INTO tickets (
                            id,
                            user_id,
                            user_name,
                            user_email,
                            airline,
                            flight_number,
                            departure_airport,
                            arrival_airport,
                            departure_time,
                            arrival_time,
                            seat_row,
                            seat_letter
                        ) VALUES (
                        (SELECT COALESCE(MAX(id), 0) + 1 FROM tickets), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                        ) RETURNING id;
                    """,
                    user_id,
                    user_name,
                    user_email,
                    airline,
                    flight_number,
                    departure_airport,
                    arrival_airport,
                    departure_time_datetime,
                    arrival_time_datetime,
                    seat_row,
                    seat_letter,
                    timeout=10,
                )
                if ticket_booking_result:
                    ticket_id = ticket_booking_result["id"]
                else:
                    raise Exception("Ticket Insertion failure")
                # Book the seat in the same transaction
                seat_booking_result = await conn.execute(
                    """
                        UPDATE seats
                        SET is_reserved = TRUE, ticket_id = $1
                        WHERE flight_id = (
                            SELECT id
                            FROM flights
                            WHERE flight_number = $2 AND
                                    airline = $3 AND
                                    departure_airport = $4 AND
                                    departure_time = $5)
                                AND seat_row = $6
                                AND seat_letter = $7
                    """,
                    ticket_id,
                    flight_number,
                    airline,
                    departure_airport,
                    departure_time_datetime,
                    seat_row,
                    seat_letter,
                    timeout=10,
                )
                if seat_booking_result != "UPDATE 1":
                    raise Exception("Ticket - Seat Update failure")

    async def list_tickets(
        self,
        user_id: str,
    ) -> list[models.Ticket]:
        results = await self.__pool.fetch(
            """
                SELECT * FROM tickets
                WHERE user_id = $1
            """,
            user_id,
            timeout=10,
        )
        results = [models.Ticket.model_validate(dict(r)) for r in results]
        return results

    async def close(self):
        await self.__pool.close()
