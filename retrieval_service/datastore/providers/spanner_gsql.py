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

import datetime
from abc import ABC, abstractmethod
from typing import Any, Literal, Optional

import models
from google.cloud import spanner  # type: ignore
from google.cloud.spanner_admin_database_v1.types import DatabaseDialect
from google.cloud.spanner_v1 import JsonObject, param_types
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.instance import Instance
from google.oauth2 import service_account  # type: ignore
from pydantic import BaseModel

from .. import datastore

# Identifier for Spanner
SPANNER_IDENTIFIER = "spanner-gsql"


class DialectSemantics(ABC):
    """
    Abstract base class for dialect semantics.
    """

    def get_database_ddl(self) -> list[str]:
        """
        Abstract method to get the Data Definition Language (DDL) statements for the database.

        Returns:
            list[str]: List of DDL statements.
        """
        raise NotImplementedError(
            "get_database_ddl method must be implemented by subclass."
        )

    def get_query_placeholder(self, num: int) -> list:
        """
        Abstract method to get placeholders for query parameters.

        Args:
            num (int): Number of placeholders to generate.

        Returns:
            list: List of placeholders.
        """
        raise NotImplementedError(
            "get_query_placeholder method must be implemented by subclass."
        )

    def get_distance_function(self) -> str:
        """
        Abstract method to get the distance function for similarity search.

        Returns:
            str: The distance function.
        """
        raise NotImplementedError(
            "get_distance_function method must be implemented by subclass."
        )


class GoogleSqlSemantics(DialectSemantics):
    """
    Implementation of dialect semantics for Google SQL.
    """

    def get_database_ddl(self) -> list[str]:
        # Initialize a list to store Data Definition Language (DDL) statements
        ddl = []

        # Create DDL statement to drop the 'airports' table if it exists
        ddl.append("DROP TABLE IF EXISTS airports")

        # Create DDL statement to create the 'airports' table
        ddl.append(
            """
            CREATE TABLE airports(
                id INT64,
                iata STRING(MAX),
                name STRING(MAX),
                city STRING(MAX),
                country STRING(MAX)
            ) PRIMARY KEY(id)
            """
        )

        # Create DDL statement to drop the 'amenities' table if it exists
        ddl.append("DROP TABLE IF EXISTS amenities")

        # Create DDL statement to create the 'amenities' table
        ddl.append(
            """
            CREATE TABLE amenities(
              id INT64,
              name STRING(MAX),
              description STRING(MAX),
              location STRING(MAX),
              terminal STRING(MAX),
              category STRING(MAX),
              hour STRING(MAX),
              sunday_start_hour STRING(100),
              sunday_end_hour STRING(100),
              monday_start_hour STRING(100),
              monday_end_hour STRING(100),
              tuesday_start_hour STRING(100),
              tuesday_end_hour STRING(100),
              wednesday_start_hour STRING(100),
              wednesday_end_hour STRING(100),
              thursday_start_hour STRING(100),
              thursday_end_hour STRING(100),
              friday_start_hour STRING(100),
              friday_end_hour STRING(100),
              saturday_start_hour STRING(100),
              saturday_end_hour STRING(100),
              content STRING(MAX) NOT NULL,
              embedding ARRAY<FLOAT64> NOT NULL
            ) PRIMARY KEY(id)
            """
        )

        # Create DDL statement to drop the 'flights' table if it exists
        ddl.append("DROP TABLE IF EXISTS flights")

        # Create DDL statement to create the 'flights' table
        ddl.append(
            """
            CREATE TABLE flights(
              id INT64,
              airline STRING(MAX),
              flight_number STRING(MAX),
              departure_airport STRING(MAX),
              arrival_airport STRING(MAX),
              departure_time STRING(100),
              arrival_time STRING(100),
              departure_gate STRING(MAX),
              arrival_gate STRING(MAX)
            ) PRIMARY KEY(id)
            """
        )

        # Create DDL statement to drop the 'policies' table if it exists
        ddl.append("DROP TABLE IF EXISTS policies")

        # Create DDL statement to create the 'policies' table
        ddl.append(
            """
            CREATE TABLE policies(
              id INT64,
              content STRING(MAX) NOT NULL,
              embedding ARRAY<FLOAT64> NOT NULL
            ) PRIMARY KEY(id)
            """
        )

        # Create DDL statement to drop the 'tickets' table if it exists
        ddl.append("DROP TABLE IF EXISTS tickets")

        # Create DDL statement to create the 'tickets' table
        ddl.append(
            """
            CREATE TABLE tickets(
              user_id STRING(MAX),
              user_name STRING(MAX),
              user_email STRING(MAX),
              airline STRING(MAX),
              flight_number STRING(MAX),
              departure_airport STRING(MAX),
              arrival_airport STRING(MAX),
              departure_time STRING(100),
              arrival_time STRING(100)
            ) PRIMARY KEY(user_id, airline, flight_number, departure_time)
            """
        )

        return ddl

    def get_query_placeholder(self, num: int) -> list:
        return [("@param" + str(i), "param" + str(i)) for i in range(1, num + 1)]

    def get_distance_function(self) -> str:
        return "COSINE_DISTANCE"


class PGSqlSemantics(DialectSemantics):
    """
    Implementation of dialect semantics for PGSQL.
    """

    def get_database_ddl(self) -> list[str]:
        # Initialize a list to store Data Definition Language (DDL) statements
        ddl = []

        # Create DDL statement to drop the 'airports' table if it exists
        ddl.append("DROP TABLE IF EXISTS airports")

        # Create DDL statement to create the 'airports' table
        ddl.append(
            """
            CREATE TABLE airports(
                id BIGINT PRIMARY KEY,
                iata VARCHAR,
                name VARCHAR,
                city VARCHAR,
                country VARCHAR
            )
            """
        )

        # Create DDL statement to drop the 'amenities' table if it exists
        ddl.append("DROP TABLE IF EXISTS amenities")

        # Create DDL statement to create the 'amenities' table
        ddl.append(
            """
            CREATE TABLE amenities(
                id BIGINT PRIMARY KEY,
                name VARCHAR,
                description VARCHAR,
                location VARCHAR,
                terminal VARCHAR,
                category VARCHAR,
                hour VARCHAR,
                sunday_start_hour VARCHAR,
                sunday_end_hour VARCHAR,
                monday_start_hour VARCHAR,
                monday_end_hour VARCHAR,
                tuesday_start_hour VARCHAR,
                tuesday_end_hour VARCHAR,
                wednesday_start_hour VARCHAR,
                wednesday_end_hour VARCHAR,
                thursday_start_hour VARCHAR,
                thursday_end_hour VARCHAR,
                friday_start_hour VARCHAR,
                friday_end_hour VARCHAR,
                saturday_start_hour VARCHAR,
                saturday_end_hour VARCHAR,
                content VARCHAR NOT NULL,
                embedding FLOAT8[] NOT NULL
            )
            """
        )

        # Create DDL statement to drop the 'flights' table if it exists
        ddl.append("DROP TABLE IF EXISTS flights")

        # Create DDL statement to create the 'flights' table
        ddl.append(
            """
            CREATE TABLE flights(
                id BIGINT PRIMARY KEY,
                airline VARCHAR,
                flight_number VARCHAR,
                departure_airport VARCHAR,
                arrival_airport VARCHAR,
                departure_time VARCHAR(100),
                arrival_time VARCHAR(100),
                departure_gate VARCHAR,
                arrival_gate VARCHAR
            )
            """
        )

        # Create DDL statement to drop the 'policies' table if it exists
        ddl.append("DROP TABLE IF EXISTS policies")

        # Create DDL statement to create the 'policies' table
        ddl.append(
            """
            CREATE TABLE policies(
                id BIGINT PRIMARY KEY,
                content VARCHAR NOT NULL,
                embedding FLOAT8[] NOT NULL
            )
            """
        )

        # Create DDL statement to drop the 'tickets' table if it exists
        ddl.append("DROP TABLE IF EXISTS tickets")

        # Create DDL statement to create the 'tickets' table
        ddl.append(
            """
            CREATE TABLE tickets(
                user_id VARCHAR,
                user_name VARCHAR,
                user_email VARCHAR,
                airline VARCHAR,
                flight_number VARCHAR,
                departure_airport VARCHAR,
                arrival_airport VARCHAR,
                departure_time VARCHAR(100),
                arrival_time VARCHAR(100),
                PRIMARY KEY(user_id, airline, flight_number, departure_time)
            )
            """
        )

        return ddl

    def get_query_placeholder(self, num: int) -> list:
        return [("$" + str(i), "p" + str(i)) for i in range(1, num + 1)]

    def get_distance_function(self) -> str:
        return "spanner.cosine_distance"


# Configuration model for Spanner
class Config(BaseModel, datastore.AbstractConfig):
    """
    Configuration model for Spanner.

    Attributes:
        kind (Literal["spanner"]): Type of datastore.
        project (str): Google Cloud project ID.
        instance (str): ID of the Spanner instance.
        database (str): ID of the Spanner database.
        service_account_key_file (str): Service Account Key File.
    """

    kind: Literal["spanner-gsql"]
    project: str
    instance: str
    database: str
    service_account_key_file: Optional[str] = None


# Client class for interacting with Spanner
class Client(datastore.Client[Config]):
    """
    Client class for interacting with Spanner.

    Attributes:
        __client (spanner.Client): Spanner client instance.
        __instance_id (str): ID of the Spanner instance.
        __database_id (str): ID of the Spanner database.
        __instance (Instance): Spanner instance.
        __database (Database): Spanner database.
    """

    OPERATION_TIMEOUT_SECONDS = 240
    BATCH_SIZE = 1000
    AIRPORT_COLUMNS = ["id", "iata", "name", "city", "country"]
    AMENITIES_COLUMNS = [
        "id",
        "name",
        "description",
        "location",
        "terminal",
        "category",
        "hour",
        "sunday_start_hour",
        "sunday_end_hour",
        "monday_start_hour",
        "monday_end_hour",
        "tuesday_start_hour",
        "tuesday_end_hour",
        "wednesday_start_hour",
        "wednesday_end_hour",
        "thursday_start_hour",
        "thursday_end_hour",
        "friday_start_hour",
        "friday_end_hour",
        "saturday_start_hour",
        "saturday_end_hour",
        "content",
        "embedding",
    ]
    FLIGHTS_COLUMNS = [
        "id",
        "airline",
        "flight_number",
        "departure_airport",
        "arrival_airport",
        "departure_time",
        "arrival_time",
        "departure_gate",
        "arrival_gate",
    ]

    POLICIES_COLUMNS = ["id", "content", "embedding"]

    @datastore.classproperty
    def kind(cls):
        return SPANNER_IDENTIFIER

    def __init__(self, client: spanner.Client, instance_id: str, database_id: str):
        """
        Initialize the Spanner client.

        Args:
            client (spanner.Client): Spanner client instance.
            instance_id (str): ID of the Spanner instance.
            database_id (str): ID of the Spanner database.
        """
        self.__client = client
        self.__instance_id = instance_id
        self.__database_id = database_id

        self.__instance = self.__client.instance(self.__instance_id)
        self.__database = self.__instance.database(self.__database_id)

        self._dialect_semantics: DialectSemantics

        if self.__database.database_dialect == DatabaseDialect.POSTGRESQL:
            self._dialect_semantics = PGSqlSemantics()
        else:
            self._dialect_semantics = GoogleSqlSemantics()

        self._placeholders = self._dialect_semantics.get_query_placeholder(20)

    @classmethod
    async def create(cls, config: Config) -> "Client":
        """
        Create a Spanner client.

        Args:
            config (Config): Configuration for creating the client.

        Returns:
            Client: Initialized Spanner client.
        """
        client: spanner.Client

        if (
            config.service_account_key_file is not None
            and config.service_account_key_file.strip() != ""
        ):
            credentials = service_account.Credentials.from_service_account_file(
                config.service_account_key_file
            )
            client = spanner.Client(project=config.project, credentials=credentials)
        else:
            client = spanner.Client(project=config.project)

        instance_id = config.instance
        instance = client.instance(instance_id)

        if not instance.exists():
            raise Exception(f"Instance with id: {instance_id} doesn't exist.")

        database_id = config.database
        database = instance.database(database_id)

        if not database.exists():
            raise Exception(f"Database with id: {database_id} doesn't exist.")

        return cls(client, instance_id, database_id)

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        """
        Initialize data in the Spanner database by creating tables and inserting records.

        Args:
            airports (list[models.Airport]): list of airports to be initialized.
            amenities (list[models.Amenity]): list of amenities to be initialized.
            flights (list[models.Flight]): list of flights to be initialized.
            policies (list[models.Policy]): list of policies to be initialized.
        Returns:
            None
        """

        # Update the schema using DDL statements
        operation = self.__database.update_ddl(
            self._dialect_semantics.get_database_ddl()
        )

        print("Waiting for schema update operation to complete...")
        operation.result(self.OPERATION_TIMEOUT_SECONDS)
        print("Schema update operation completed")

        # Insert data into 'airports' table using batch operation

        values = [
            tuple(getattr(airport, field) for field in self.AIRPORT_COLUMNS)
            for airport in airports
        ]

        for i in range(0, len(values), self.BATCH_SIZE):
            records = values[i : i + self.BATCH_SIZE]

            with self.__database.batch() as batch:
                batch.insert(
                    table="airports",
                    columns=self.AIRPORT_COLUMNS,
                    values=records,
                )

        # Insert data into 'amenities' table using batch operation
        values = [
            tuple(
                (
                    str(getattr(amenity, field))
                    if isinstance(getattr(amenity, field), datetime.time)
                    else getattr(amenity, field)
                )
                for field in self.AMENITIES_COLUMNS
            )
            for amenity in amenities
        ]

        for i in range(0, len(values), self.BATCH_SIZE):
            records = values[i : i + self.BATCH_SIZE]

            with self.__database.batch() as batch:
                batch.insert(
                    table="amenities",
                    columns=self.AMENITIES_COLUMNS,
                    values=records,
                )

        # Insert data into 'flights' table using batch operation
        values = [
            tuple(
                (
                    str(getattr(flight, field))
                    if isinstance(getattr(flight, field), datetime.datetime)
                    else getattr(flight, field)
                )
                for field in self.FLIGHTS_COLUMNS
            )
            for flight in flights
        ]

        for i in range(0, len(values), self.BATCH_SIZE):
            records = values[i : i + self.BATCH_SIZE]

            with self.__database.batch() as batch:
                batch.insert(
                    table="flights",
                    columns=self.FLIGHTS_COLUMNS,
                    values=records,
                )

        # Insert data into 'policies' table using batch operation
        values = [
            tuple(getattr(policy, field) for field in self.POLICIES_COLUMNS)
            for policy in policies
        ]

        for i in range(0, len(values), self.BATCH_SIZE):
            records = values[i : i + self.BATCH_SIZE]

            with self.__database.batch() as batch:
                batch.insert(
                    table="policies",
                    columns=self.POLICIES_COLUMNS,
                    values=records,
                )

        # Return None to indicate successful initialization
        return None

    async def export_data(
        self,
    ) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        """
        Export data from the Spanner database.

        Returns:
            tuple: A tuple containing lists of airports, amenities, flights, and policies.
        """
        airports: list = []
        amenities: list = []
        flights: list = []
        policies: list = []

        try:
            with self.__database.snapshot() as snapshot:
                # Execute SQL queries to fetch data from respective tables
                airport_results = snapshot.execute_sql(
                    "SELECT {} FROM airports ORDER BY id ASC".format(
                        ",".join(self.AIRPORT_COLUMNS)
                    )
                )
        except Exception as e:
            # Handle any exceptions, such as database connection errors
            print(f"Error occurred while fetch airports: {e}")
            # Return empty lists in case of error
            return airports, amenities, flights, policies

        # Convert query results to model instances using model_validate method
        airports = [
            models.Airport.model_validate(
                {key: value for key, value in zip(self.AIRPORT_COLUMNS, a)}
            )
            for a in airport_results
        ]

        try:
            with self.__database.snapshot() as snapshot:
                # Execute SQL queries to fetch data from respective tables
                amenity_results = snapshot.execute_sql(
                    "SELECT {} FROM amenities ORDER BY id ASC".format(
                        ",".join(self.AMENITIES_COLUMNS)
                    )
                )
        except Exception as e:
            # Handle any exceptions, such as database connection errors
            print(f"Error occurred while fetch amenities: {e}")
            # Return empty lists in case of error
            return airports, amenities, flights, policies

        # Convert query results to model instances using model_validate method
        amenities = [
            models.Amenity.model_validate(
                {key: value for key, value in zip(self.AMENITIES_COLUMNS, a)}
            )
            for a in amenity_results
        ]

        try:
            with self.__database.snapshot() as snapshot:
                # Execute SQL queries to fetch data from respective tables
                flights_results = snapshot.execute_sql(
                    "SELECT {} FROM flights ORDER BY id ASC".format(
                        ",".join(self.FLIGHTS_COLUMNS)
                    )
                )
        except Exception as e:
            # Handle any exceptions, such as database connection errors
            print(f"Error occurred while fetch flights: {e}")
            # Return empty lists in case of error
            return airports, amenities, flights, policies

        # Convert query results to model instances using model_validate method
        flights = [
            models.Flight.model_validate(
                {key: value for key, value in zip(self.FLIGHTS_COLUMNS, a)}
            )
            for a in flights_results
        ]

        try:
            with self.__database.snapshot() as snapshot:
                # Execute SQL queries to fetch data from respective tables
                policy_results = snapshot.execute_sql(
                    "SELECT {} FROM policies ORDER BY id ASC".format(
                        ",".join(self.POLICIES_COLUMNS)
                    )
                )
        except Exception as e:
            # Handle any exceptions, such as database connection errors
            print(f"Error occurred while fetch policies: {e}")
            # Return empty lists in case of error
            return airports, amenities, flights, policies

        # Convert query results to model instances using model_validate method
        policies = [
            models.Policy.model_validate(
                {key: value for key, value in zip(self.POLICIES_COLUMNS, a)}
            )
            for a in policy_results
        ]

        return airports, amenities, flights, policies

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        """
        Retrieve an airport by its ID.

        Args:
            id (int): The ID of the airport.

        Returns:
            Optional[models.Airport]: An Airport model instance if found, else None.
        """
        with self.__database.snapshot() as snapshot:
            # Execute SQL query to fetch airport by ID
            result = snapshot.execute_sql(
                sql="SELECT * FROM airports WHERE id = {}".format(
                    self._placeholders[0][0]
                ),
                params={self._placeholders[0][1]: id},
                param_types={self._placeholders[0][1]: param_types.INT64},
            )

        # Check if result is None
        if result is None:
            return None

        # Convert query result to model instance using model_validate method
        airports = [
            models.Airport.model_validate(
                {key: value for key, value in zip(self.AIRPORT_COLUMNS, a)}
            )
            for a in result
        ]

        return airports[0]

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        """
        Retrieve an airport by its IATA code.

        Args:
            iata (str): The IATA code of the airport.

        Returns:
            Optional[models.Airport]: An Airport model instance if found, else None.
        """
        with self.__database.snapshot() as snapshot:
            # Execute SQL query to fetch airport by ID
            result = snapshot.execute_sql(
                sql="SELECT * FROM airports WHERE LOWER(iata) LIKE LOWER({})".format(
                    self._placeholders[0][0]
                ),
                params={self._placeholders[0][1]: iata},
                param_types={self._placeholders[0][1]: param_types.STRING},
            )

        # Check if result is None
        if result is None:
            return None

        # Convert query result to model instance using model_validate method
        airports = [
            models.Airport.model_validate(
                {key: value for key, value in zip(self.AIRPORT_COLUMNS, a)}
            )
            for a in result
        ]

        return airports[0]

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        """
        Search for airports based on optional parameters.

        Args:
            country (Optional[str]): The country of the airport.
            city (Optional[str]): The city of the airport.
            name (Optional[str]): The name of the airport.

        Returns:
            list[models.Airport]: A list of Airport model instances matching the search criteria.
        """
        with self.__database.snapshot() as snapshot:
            # Construct SQL query based on provided parameters
            query = """
                SELECT * FROM airports
                  WHERE (COALESCE({country}) IS NULL OR LOWER(country) LIKE LOWER({country}))
                  AND (COALESCE({city}) IS NULL OR LOWER(city) LIKE LOWER({city}))
                  AND (COALESCE({name}) IS NULL OR LOWER(name) LIKE '%' || LOWER({name}) || '%')
                """.format(
                country=self._placeholders[0][0],
                city=self._placeholders[1][0],
                name=self._placeholders[2][0],
            )

            # Execute SQL query with parameters
            results = snapshot.execute_sql(
                sql=query,
                params={
                    self._placeholders[0][1]: country,
                    self._placeholders[1][1]: city,
                    self._placeholders[2][1]: name,
                },
                param_types={
                    self._placeholders[0][1]: param_types.STRING,
                    self._placeholders[1][1]: param_types.STRING,
                    self._placeholders[2][1]: param_types.STRING,
                },
            )

        # Convert query result to model instance using model_validate method
        airports = [
            models.Airport.model_validate(
                {key: value for key, value in zip(self.AIRPORT_COLUMNS, a)}
            )
            for a in results
        ]

        return airports

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        """
        Retrieves an amenity by its ID.

        Args:
            id (int): The ID of the amenity.

        Returns:
            Optional[models.Amenity]: An Amenity model instance if found, else None.
        """

        with self.__database.snapshot() as snapshot:
            # Spread SQL query for readability
            result = snapshot.execute_sql(
                sql="""
                SELECT * FROM amenities
                WHERE id = {}
                """.format(
                    self._placeholders[0][0]
                ),
                params={self._placeholders[0][1]: id},
                param_types={self._placeholders[0][1]: param_types.INT64},
            )

        # Check if result is None
        if result is None:
            return None

        # Convert query result to model instance using model_validate method
        amenities = [
            models.Amenity.model_validate(
                {key: value for key, value in zip(self.AMENITIES_COLUMNS, a)}
            )
            for a in result
        ]

        return amenities[0]

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[Any]:
        """
        Search for amenities based on similarity to a query embedding.

        Args:
            query_embedding (list[float]): The embedding representing the query.
            similarity_threshold (float): The minimum similarity threshold for results.
            top_k (int): The maximum number of results to return.

        Returns:
            list[models.Amenity]: A list of Amenity model instances matching the search criteria.
        """
        with self.__database.snapshot() as snapshot:
            # Spread SQL query for readability
            query = """
                SELECT name, description, location, terminal, category, hour
                FROM (
                    SELECT name, description, location, terminal, category, hour,
                       {distance}(embedding, {query_embedding}) AS similarity
                    FROM amenities
                ) AS sorted_amenities
                WHERE (1 - similarity) > {similarity_threshold}
                ORDER BY similarity
                LIMIT {top_k}
            """.format(
                distance=self._dialect_semantics.get_distance_function(),
                query_embedding=self._placeholders[0][0],
                similarity_threshold=self._placeholders[1][0],
                top_k=self._placeholders[2][0],
            )

            # Execute SQL query with parameters
            results = snapshot.execute_sql(
                sql=query,
                params={
                    self._placeholders[0][1]: query_embedding,
                    self._placeholders[1][1]: similarity_threshold,
                    self._placeholders[2][1]: top_k,
                },
                param_types={
                    self._placeholders[0][1]: param_types.Array(param_types.FLOAT64),
                    self._placeholders[1][1]: param_types.FLOAT64,
                    self._placeholders[2][1]: param_types.INT64,
                },
            )

        # Convert query result to model instance using model_validate method
        amenities = [
            {key: value for key, value in zip(self.AMENITIES_COLUMNS[1:], a)}
            for a in results
        ]

        return amenities

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        """
        Retrieves a flight by its ID.

        Args:
            flight_id (int): The ID of the flight.

        Returns:
            Optional[models.Flight]: A Flight model instance if found, else None.
        """
        with self.__database.snapshot() as snapshot:
            # Spread SQL query for readability
            result = snapshot.execute_sql(
                sql="""
                SELECT * FROM flights
                WHERE id = {}
                """.format(
                    self._placeholders[0][0]
                ),
                params={self._placeholders[0][1]: flight_id},
                param_types={self._placeholders[0][1]: param_types.INT64},
            )
        # Check if result is None
        if result is None:
            return None

        # Convert query result to model instance using model_validate method
        flights = [
            models.Flight.model_validate(
                {key: value for key, value in zip(self.FLIGHTS_COLUMNS, a)}
            )
            for a in result
        ]

        return flights[0]

    async def search_flights_by_number(
        self,
        airline: str,
        number: str,
    ) -> list[models.Flight]:
        """
        Search for flights by airline and flight number.

        Args:
            airline (str): The airline of the flight.
            number (str): The flight number.

        Returns:
            list[models.Flight]: A list of Flight model instances matching the search criteria.
        """
        with self.__database.snapshot() as snapshot:
            # Spread SQL query for readability
            results = snapshot.execute_sql(
                sql="""
                SELECT * FROM flights
                WHERE airline = {}
                AND flight_number = {}
                """.format(
                    self._placeholders[0][0], self._placeholders[1][0]
                ),
                params={
                    self._placeholders[0][1]: airline,
                    self._placeholders[1][1]: number,
                },
                param_types={
                    self._placeholders[0][1]: param_types.STRING,
                    self._placeholders[1][1]: param_types.STRING,
                },
            )

        # Convert query result to model instance using model_validate method
        flights = [
            models.Flight.model_validate(
                {key: value for key, value in zip(self.FLIGHTS_COLUMNS, a)}
            )
            for a in results
        ]

        return flights

    async def search_flights_by_airports(
        self,
        date: str,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        """
        Search for flights by departure and/or arrival airports.

        Args:
            date (str): The date of the flights in 'YYYY-MM-DD' format.
            departure_airport (str, optional): The departure airport code. Defaults to None.
            arrival_airport (str, optional): The arrival airport code. Defaults to None.

        Returns:
            list[models.Flight]: A list of Flight model instances matching the search criteria.
        """
        with self.__database.snapshot() as snapshot:
            # Spread SQL query for readability
            query = """
                SELECT * FROM flights
                WHERE (COALESCE({departure_airport}) IS NULL OR LOWER(departure_airport) LIKE LOWER({departure_airport}))
                AND (COALESCE({arrival_airport}) IS NULL OR LOWER(arrival_airport) LIKE LOWER({arrival_airport}))
                AND cast(departure_time as TIMESTAMP) >= CAST({datetime} AS TIMESTAMP)
                AND cast(departure_time as TIMESTAMP) < TIMESTAMP_ADD(CAST({datetime} AS TIMESTAMP), INTERVAL 1 DAY)
                LIMIT 10
            """

            if isinstance(self._dialect_semantics, PGSqlSemantics):
                query = """
                    SELECT * FROM flights
                    WHERE (COALESCE({departure_airport}) IS NULL OR LOWER(departure_airport) LIKE LOWER({departure_airport}))
                    AND (COALESCE({arrival_airport}) IS NULL OR LOWER(arrival_airport) LIKE LOWER({arrival_airport}))
                    AND CAST(departure_time as timestamptz) >= CAST({datetime} AS timestamptz)
                    AND cast(departure_time as timestamptz) < spanner.timestamptz_add(CAST({datetime} AS timestamptz), '1 day')
                    """

            query = query.format(
                departure_airport=self._placeholders[0][0],
                arrival_airport=self._placeholders[1][0],
                datetime=self._placeholders[2][0],
            )

            # Execute SQL query with parameters
            results = snapshot.execute_sql(
                sql=query,
                params={
                    self._placeholders[0][1]: departure_airport,
                    self._placeholders[1][1]: arrival_airport,
                    self._placeholders[2][1]: date,
                },
                param_types={
                    self._placeholders[0][1]: param_types.STRING,
                    self._placeholders[1][1]: param_types.STRING,
                    self._placeholders[2][1]: param_types.STRING,
                },
            )

        # Convert query results to model instances using model_validate method
        flights = [
            models.Flight.model_validate(
                {key: value for key, value in zip(self.FLIGHTS_COLUMNS, a)}
            )
            for a in results
        ]

        return flights

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        arrival_airport: str,
        departure_time: datetime.datetime,
        arrival_time: datetime.datetime,
    ) -> bool:
        with self.__database.snapshot() as snapshot:
            # Spread SQL query for readability
            results = snapshot.execute_sql(
                sql="""
                    SELECT * FROM flights
                    WHERE LOWER(airline) LIKE LOWER({})
                    AND LOWER(flight_number) LIKE LOWER({})
                    AND LOWER(departure_airport) LIKE LOWER({})
                    AND LOWER(arrival_airport) LIKE LOWER({})
                    AND departure_time = {}
                    AND arrival_time = {}
                """.format(
                    self._placeholders[0][0],
                    self._placeholders[1][0],
                    self._placeholders[2][0],
                    self._placeholders[3][0],
                    self._placeholders[4][0],
                    self._placeholders[5][0],
                ),
                params={
                    self._placeholders[0][1]: airline,
                    self._placeholders[1][1]: flight_number,
                    self._placeholders[2][1]: departure_airport,
                    self._placeholders[3][1]: arrival_airport,
                    self._placeholders[4][1]: departure_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    self._placeholders[5][1]: arrival_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                },
                param_types={
                    self._placeholders[0][1]: param_types.STRING,
                    self._placeholders[1][1]: param_types.STRING,
                    self._placeholders[2][1]: param_types.STRING,
                    self._placeholders[3][1]: param_types.STRING,
                    self._placeholders[4][1]: param_types.STRING,
                    self._placeholders[5][1]: param_types.STRING,
                },
            )

        flights = [x for x in results]

        if len(flights) == 1:
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
    ):
        """
        Inserts a ticket into the database.

        Args:
            user_id (str): The ID of the user.
            user_name (str): The name of the user.
            user_email (str): The email of the user.
            airline (str): The airline of the flight.
            flight_number (str): The flight number.
            departure_airport (str): The departure airport code.
            arrival_airport (str): The arrival airport code.
            departure_time (str): The departure time of the flight.
            arrival_time (str): The arrival time of the flight.
        """
        departure_time_datetime = datetime.datetime.strptime(
            departure_time, "%Y-%m-%d %H:%M:%S"
        )
        arrival_time_datetime = datetime.datetime.strptime(
            arrival_time, "%Y-%m-%d %H:%M:%S"
        )

        if not await self.validate_ticket(
            airline,
            flight_number,
            departure_airport,
            arrival_airport,
            departure_time_datetime,
            arrival_time_datetime,
        ):
            raise Exception("Flight information not in database")

        with self.__database.batch() as batch:
            batch.insert(
                table="tickets",
                columns=[
                    "user_id",
                    "user_name",
                    "user_email",
                    "airline",
                    "flight_number",
                    "departure_airport",
                    "arrival_airport",
                    "departure_time",
                    "arrival_time",
                ],
                values=[
                    [
                        user_id,
                        user_name,
                        user_email,
                        airline,
                        flight_number,
                        departure_airport,
                        arrival_airport,
                        departure_time_datetime,
                        arrival_time_datetime,
                    ]
                ],
            )

    async def list_tickets(
        self,
        user_id: str,
    ) -> list[models.Ticket]:
        """
        Retrieves a list of tickets for a user.

        Args:
            user_id (str): The ID of the user.
        """
        with self.__database.snapshot() as snapshot:
            # Spread SQL query for readability
            results = snapshot.execute_sql(
                sql="""
                SELECT * FROM tickets
                WHERE user_id = {}
                """.format(
                    self._placeholders[0][0]
                ),
                params={self._placeholders[0][1]: user_id},
                param_types={self._placeholders[0][1]: param_types.STRING},
            )

        # Convert query results to model instances using model_validate method
        tickets = [
            models.Ticket.model_validate(
                {
                    key: value
                    for key, value in zip(
                        [
                            "user_id",
                            "user_name",
                            "user_email",
                            "airline",
                            "flight_number",
                            "departure_airport",
                            "arrival_airport",
                            "departure_time",
                            "arrival_time",
                        ],
                        a,
                    )
                }
            )
            for a in results
        ]

        return tickets

    async def policies_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[str]:
        """
        Search for policies based on similarity to a query embedding.

        Args:
            query_embedding (list[float]): The embedding representing the query.
            similarity_threshold (float): The minimum similarity threshold for results.
            top_k (int): The maximum number of results to return.

        Returns:
            list[models.Policy]: A list of Policy model instances matching the search criteria.
        """
        with self.__database.snapshot() as snapshot:
            query = """
                SELECT content
                FROM (
                    SELECT content,  {distance}(embedding, {query_embedding}) AS similarity
                    FROM policies 
                ) AS sorted_policies
                WHERE (1 - similarity) > {similarity_threshold}
                ORDER BY similarity
                LIMIT {top_k}
            """.format(
                distance=self._dialect_semantics.get_distance_function(),
                query_embedding=self._placeholders[0][0],
                similarity_threshold=self._placeholders[1][0],
                top_k=self._placeholders[2][0],
            )

            # Execute SQL query with parameters
            results = snapshot.execute_sql(
                sql=query,
                params={
                    self._placeholders[0][1]: query_embedding,
                    self._placeholders[1][1]: similarity_threshold,
                    self._placeholders[2][1]: top_k,
                },
                param_types={
                    self._placeholders[0][1]: param_types.Array(param_types.FLOAT64),
                    self._placeholders[1][1]: param_types.FLOAT64,
                    self._placeholders[2][1]: param_types.INT64,
                },
            )

        # Convert query result to model instance using model_validate method
        policies = [a[0] for a in results]

        return policies

    async def close(self):
        """
        Closes the database client connection.
        """
        self.__client.close()
