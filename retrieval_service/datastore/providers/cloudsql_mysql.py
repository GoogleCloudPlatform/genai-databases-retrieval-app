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
from typing import Any, Literal, Optional

from google.cloud.sql.connector import Connector
from pydantic import BaseModel
from sqlalchemy import text, create_engine, Engine
from sqlalchemy.engine.base import Engine

import pymysql
import models

from .. import datastore

MYSQL_IDENTIFIER = "cloudsql-mysql"

class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["cloudsql-mysql"]
    project: str
    region: str
    instance: str
    user: str
    password: str
    database: str


class Client(datastore.Client[Config]):
    __pool: Engine

    @datastore.classproperty
    def kind(cls):
        return "cloudsql-mysql"

    def __init__(self, pool: Engine):
        self.__pool = pool

    @classmethod
    def create_sync(cls, config: Config) -> "Client":
        def getconn() -> pymysql.Connection:
            with Connector() as connector:
                conn: pymysql.Connection = connector.connect(
                    # Cloud SQL instance connection name
                    f"{config.project}:{config.region}:{config.instance}",
                    "pymysql",
                    user=f"{config.user}",
                    password=f"{config.password}",
                    db=f"{config.database}",
                    autocommit=True,
                )
            return conn

        pool = create_engine(
            "mysql+pymysql://",
            creator=getconn,
        )
        if pool is None:
            raise TypeError("pool not instantiated")
        return cls(pool)

    @classmethod
    async def create(cls, config: Config) -> "Client":
        loop = asyncio.get_running_loop()

        pool = await loop.run_in_executor(None, cls.create_sync, config)
        return pool

    def initialize_data_sync(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        with self.__pool.connect() as conn:
            # If the table already exists, drop it to avoid conflicts
            conn.execute(text("DROP TABLE IF EXISTS airports"))
            # Create a new table
            conn.execute(
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
            conn.execute(
                text(
                    """INSERT INTO airports VALUES (:id, :iata, :name, :city, :country)"""
                ),parameters=[{
                        "id": a.id,
                        "iata": a.iata,
                        "name": a.name,
                        "city": a.city,
                        "country": a.country,
                    } for a in airports]
            )

            # If the table already exists, drop it to avoid conflicts
            conn.execute(text("DROP TABLE IF EXISTS amenities CASCADE"))
            
            # Create a new table
            conn.execute(
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
                      embedding vector(768) USING VARBINARY NOT NULL
                    )
                    """
                )
            )
    
            # Insert all the data
            conn.execute(
                text(
                    """
                    INSERT INTO amenities VALUES (:id, :name, :description, :location,
                    :terminal, :category, :hour, :sunday_start_hour, :sunday_end_hour,
                    :monday_start_hour, :monday_end_hour, :tuesday_start_hour,
                    :tuesday_end_hour, :wednesday_start_hour, :wednesday_end_hour,
                    :thursday_start_hour, :thursday_end_hour, :friday_start_hour,
                    :friday_end_hour, :saturday_start_hour, :saturday_end_hour, :content, string_to_vector(:embedding))
                    """
                ),parameters=[{
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
                        "embedding": f"{a.embedding}",
                    } for a in amenities]
            )

            # Create a vector index for the embeddings column
            conn.execute(text("CALL mysql.create_vector_index('amenities_index', 'assistantdemo.amenities', 'embedding', '')"))

            # If the table already exists, drop it to avoid conflicts
            conn.execute(text("DROP TABLE IF EXISTS flights"))
            # Create a new table
            conn.execute(
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
            conn.execute(
                text(
                    """
                    INSERT INTO flights VALUES (:id, :airline, :flight_number,
                    :departure_airport, :arrival_airport, :departure_time,
                    :arrival_time, :departure_gate, :arrival_gate)
                    """
                ),parameters=[{
                        "id": f.id,
                        "airline": f.airline,
                        "flight_number": f.flight_number,
                        "departure_airport": f.departure_airport,
                        "arrival_airport": f.arrival_airport,
                        "departure_time": f.departure_time,
                        "arrival_time": f.arrival_time,
                        "departure_gate": f.departure_gate,
                        "arrival_gate": f.arrival_gate,
                    } for f in flights]
            )

            # If the table already exists, drop it to avoid conflicts
            conn.execute(text("DROP TABLE IF EXISTS tickets"))
            # Create a new table
            conn.execute(
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
            conn.execute(text("DROP TABLE IF EXISTS policies"))
            # Create a new table
            conn.execute(
                text(
                    """
                    CREATE TABLE policies(
                      id INT PRIMARY KEY,
                      content TEXT NOT NULL,
                      embedding vector(768) USING VARBINARY NOT NULL
                    )
                    """
                )
            )
            # Insert all the data
            conn.execute(
                text(
                    """
                    INSERT INTO policies VALUES (:id, :content, string_to_vector(:embedding))
                    """
                ),parameters=[{
                        "id": p.id,
                        "content": p.content,
                        "embedding": f"{p.embedding}",
                    } for p in policies])
            
            # Create a vector index on the embedding column
            conn.execute(text("CALL mysql.create_vector_index('policies_index', 'assistantdemo.policies', 'embedding', '')"))

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.initialize_data_sync, airports, amenities, flights, policies)

    def export_data_sync(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        with self.__pool.connect() as conn:
            airport_task = conn.execute(text("""SELECT * FROM airports ORDER BY id ASC"""))
            amenity_task = conn.execute(text("""
                                             SELECT id,
                                                    name,
                                                    description,
                                                    location,
                                                    terminal,
                                                    category,
                                                    hour,
                                                    DATE_FORMAT(sunday_start_hour,  '%H:%i') AS sunday_start_hour,
                                                    DATE_FORMAT(sunday_end_hour,    '%H:%i') AS sunday_end_hour,
                                                    DATE_FORMAT(monday_start_hour,  '%H:%i') AS monday_start_hour,
                                                    DATE_FORMAT(monday_end_hour,    '%H:%i') AS monday_end_hour,
                                                    DATE_FORMAT(tuesday_start_hour, '%H:%i') AS tuesday_start_hour,
                                                    DATE_FORMAT(tuesday_end_hour,   '%H:%i') AS tuesday_end_hour,
                                                    DATE_FORMAT(wednesday_start_hour, '%H:%i') AS wednesday_start_hour,
                                                    DATE_FORMAT(wednesday_end_hour,   '%H:%i') AS wednesday_end_hour,
                                                    DATE_FORMAT(thursday_start_hour,  '%H:%i') AS thursday_start_hour,
                                                    DATE_FORMAT(thursday_end_hour,    '%H:%i') AS thursday_end_hour,
                                                    DATE_FORMAT(friday_start_hour,   '%H:%i') AS friday_start_hour,
                                                    DATE_FORMAT(friday_end_hour,     '%H:%i') AS friday_end_hour,
                                                    DATE_FORMAT(saturday_start_hour,  '%H:%i') AS saturday_start_hour,
                                                    DATE_FORMAT(saturday_end_hour,    '%H:%i') AS saturday_end_hour, 
                                                    content,
                                                    vector_to_string(embedding) as embedding
                                              FROM amenities ORDER BY id ASC
                                             """))
            flights_task = conn.execute(text("""SELECT * FROM flights ORDER BY id ASC"""))
            policy_task = conn.execute(text("""SELECT id, content, vector_to_string(embedding) as embedding FROM policies ORDER BY id ASC"""))

            airport_results = (airport_task).mappings().fetchall()
            amenity_results = (amenity_task).mappings().fetchall()
            flights_results = (flights_task).mappings().fetchall()
            policy_results = (policy_task).mappings().fetchall()

            airports = [models.Airport.model_validate(a) for a in airport_results]
            amenities = [models.Amenity.model_validate(a) for a in amenity_results]
            flights = [models.Flight.model_validate(f) for f in flights_results]
            policies = [models.Policy.model_validate(p) for p in policy_results]

            return airports, amenities, flights, policies
        
    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.export_data_sync)
        return res
    
    def get_airport_by_id_sync(self, id: int) -> Optional[models.Airport]:
        with self.__pool.connect() as conn:
            s = text("""SELECT * FROM airports WHERE id=:id""")
            params = {"id" : id}
            result = (conn.execute(s, params)).mappings().fetchone()

        if result is None:
            return None

        res = models.Airport.model_validate(result)
        return res
    
    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.get_airport_by_id_sync, id)
        return res

    def get_airport_by_iata_sync(self, iata: str) -> Optional[models.Airport]:
        with self.__pool.connect() as conn:
            s = text("""SELECT * FROM airports WHERE LOWER(iata) LIKE LOWER(:iata)""")
            params = {"iata": iata}
            result = (conn.execute(s, params)).mappings().fetchone()

        if result is None:
            return None

        res = models.Airport.model_validate(result)
        return res

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.get_airport_by_iata_sync, iata)
        return res
    
    def search_airports_sync(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        with self.__pool.connect() as conn:
            s = text(
                """
               SELECT * FROM airports
                WHERE (:country IS NULL OR LOWER(country) LIKE CONCAT('%', LOWER(:country), '%'))
                AND (:city IS NULL OR LOWER(city) LIKE CONCAT('%', LOWER(:city), '%'))
                AND (:name IS NULL OR LOWER(name) LIKE CONCAT('%', LOWER(:name), '%'))
                LIMIT 10;
                """
            )
            params = {
                "country": country,
                "city": city,
                "name": name,
            }
            results = (conn.execute(s, parameters=params)).mappings().fetchall()

        res = [models.Airport.model_validate(r) for r in results]
        return res

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.search_airports_sync, country, city, name)
        return res

    def get_amenity_sync(self, id: int) -> Optional[models.Amenity]:
        with self.__pool.connect() as conn:
            s = text(
                """
                SELECT id, name, description, location, terminal, category, hour
                FROM amenities WHERE id=:id
                """
            )
            params = {"id" : id}
            result = (conn.execute(s, parameters=params)).mappings().fetchone()

        if result is None:
            return None

        res = models.Amenity.model_validate(result)
        return res

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.get_amenity_sync, id)
        return res

    def amenities_search_sync(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[Any]:
        with self.__pool.connect() as conn:
            s = text(
                """
                SELECT name, description, location, terminal, category, hour
                  FROM amenities
                  WHERE NEAREST(embedding) TO (string_to_vector(:query), :search_options)
                """
            )
            params = {
                    "query": f"{query_embedding}",
                    "search_options": f"num_neighbors={top_k}"
                }
            results = (conn.execute(s, parameters=params)).mappings().fetchall()

        res = [r for r in results]
        return res

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[Any]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.amenities_search_sync, query_embedding, similarity_threshold, top_k)
        return res
    
    def get_flight_sync(self, flight_id: int) -> Optional[models.Flight]:
        with self.__pool.connect() as conn:
            s = text(
                """
                SELECT * FROM flights
                  WHERE id = :flight_id
                """
            )
            params = {"flight_id": flight_id}
            result = (conn.execute(s, parameters=params)).mappings().fetchone()

        if result is None:
            return None

        res = models.Flight.model_validate(result)
        return res
        
    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.get_flight_sync, flight_id)
        return res
        
    def search_flights_by_number_sync(
        self,
        airline: str,
        number: str,
    ) -> list[models.Flight]:
        with self.__pool.connect() as conn:
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
            results = (conn.execute(s, parameters=params)).mappings().fetchall()

        res = [models.Flight.model_validate(r) for r in results]
        return res
    
    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> list[models.Flight]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.search_flights_by_number_sync, airline, number)
        return res
    
    def search_flights_by_airports_sync(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        with self.__pool.connect() as conn:
            s = text(
                """
                SELECT * FROM flights
                  WHERE (CAST(:departure_airport AS CHAR(255)) IS NULL OR LOWER(departure_airport) LIKE LOWER(:departure_airport))
                  AND (CAST(:arrival_airport AS CHAR(255)) IS NULL OR LOWER(arrival_airport) LIKE LOWER(:arrival_airport))
                  AND departure_time >= CAST(:datetime AS DATETIME)
                  AND (departure_time < DATE_ADD(CAST(:datetime AS DATETIME), interval 1 day))
                  LIMIT 10
                """
            )
            params = {
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "datetime": datetime.strptime(date, "%Y-%m-%d"),
            }

            results = (conn.execute(s, parameters=params)).mappings().fetchall()

        res = [models.Flight.model_validate(r) for r in results]
        return res
    
    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.search_flights_by_airports_sync, date, departure_airport, arrival_airport)
        return res 
    
    def validate_ticket_sync(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
    ) -> Optional[models.Flight]:
        raise NotImplementedError("Not Implemented")

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
    ) -> Optional[models.Flight]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.validate_ticket_sync, airline, flight_number, departure_airport, departure_time)
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
        raise NotImplementedError("Not Implemented")

    async def list_tickets(
        self,
        user_id: str,
    ) -> list[models.Ticket]:
        raise NotImplementedError("Not Implemented")

    def policies_search_sync(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[str]:
        with self.__pool.connect() as conn:
            s = text(
                """
                SELECT content
                  FROM policies 
                  WHERE NEAREST(embedding) TO (string_to_vector(:query), :search_options)
                """
            )
            params = {
                    "query": f"{query_embedding}",
                    "search_options": f"num_neighbors={top_k}"
                }

            results = (conn.execute(s, parameters=params)).mappings().fetchall()

        res = [r["content"] for r in results]
        return res

    async def policies_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[str]:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.policies_search_sync, query_embedding, similarity_threshold, top_k)
        return res 
    
    async def close(self):
        # Vector indexes must be dropped before any DDLs on the base table are permitted
        with self.__pool.connect() as conn:
            s = text(
                """
                CALL mysql.drop_vector_index(:index_name)
                """
            )
            params = [
                {"index_name": "assistantdemo.amenities_index"},
                {"index_name": "assistantdemo.policies_index"},
            ]

            conn.execute(s, parameters=params)
        self.__pool.dispose()