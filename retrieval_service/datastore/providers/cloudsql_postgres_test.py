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
from ipaddress import IPv4Address
from typing import Any, AsyncGenerator, List

import asyncpg
import pytest
import pytest_asyncio
from csv_diff import compare, load_csv  # type: ignore
from google.cloud.sql.connector import Connector

import models
from helpers import UIFriendlyLogger

from .. import datastore
from . import cloudsql_postgres
from .test_data import (
    amenities_query_embedding1,
    amenities_query_embedding2,
    foobar_query_embedding,
    policies_query_embedding1,
    policies_query_embedding2,
)
from .utils import get_env_var

pytestmark = pytest.mark.asyncio(scope="module")


@pytest.fixture(scope="module")
def db_user() -> str:
    return get_env_var("DB_USER", "name of a postgres user")


@pytest.fixture(scope="module")
def db_pass() -> str:
    return get_env_var("DB_PASS", "password for the postgres user")


@pytest.fixture(scope="module")
def db_project() -> str:
    return get_env_var("DB_PROJECT", "project id for google cloud")


@pytest.fixture(scope="module")
def db_region() -> str:
    return get_env_var("DB_REGION", "region for cloud sql instance")


@pytest.fixture(scope="module")
def db_instance() -> str:
    return get_env_var("DB_INSTANCE", "instance for cloud sql")


@pytest.fixture(scope="module")
async def create_db(
    db_user: str, db_pass: str, db_project: str, db_region: str, db_instance: str
) -> AsyncGenerator[str, None]:
    db_name = get_env_var("DB_NAME", "name of a postgres database")
    loop = asyncio.get_running_loop()
    connector = Connector(loop=loop)
    # Database does not exist, create it.
    sys_conn: asyncpg.Connection = await connector.connect_async(
        f"{db_project}:{db_region}:{db_instance}",
        "asyncpg",
        user=f"{db_user}",
        password=f"{db_pass}",
        db="postgres",
    )
    await sys_conn.execute(f'DROP DATABASE IF EXISTS "{db_name}";')
    await sys_conn.execute(f'CREATE DATABASE "{db_name}";')
    await sys_conn.close()
    conn: asyncpg.Connection = await connector.connect_async(
        f"{db_project}:{db_region}:{db_instance}",
        "asyncpg",
        user=f"{db_user}",
        password=f"{db_pass}",
        db=f"{db_name}",
    )
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    yield db_name
    await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}";')
    await conn.close()


@pytest_asyncio.fixture(scope="module")
async def ds(
    create_db: AsyncGenerator[str, None],
    db_user: str,
    db_pass: str,
    db_project: str,
    db_region: str,
    db_instance: str,
) -> AsyncGenerator[datastore.Client, None]:
    db_name = await create_db.__anext__()
    cfg = cloudsql_postgres.Config(
        kind="cloudsql-postgres",
        user=db_user,
        password=db_pass,
        database=db_name,
        project=db_project,
        region=db_region,
        instance=db_instance,
    )
    t = create_db
    ds = await datastore.create(cfg)

    bucket_path = "cloud-samples-data"
    flights_blob_path = "databases-golden-demo/flights_dataset.csv"
    tickets_blob_path = "databases-golden-demo/tickets_dataset.csv"
    seats_blob_path = "databases-golden-demo/seats_dataset.csv"

    airports_ds_path = "../data/airport_dataset.csv"
    amenities_ds_path = "../data/amenity_dataset.csv"
    policies_ds_path = "../data/cymbalair_policy.csv"

    airports, amenities, policies, flights, tickets, seats = await ds.load_dataset(
        bucket_path,
        airports_ds_path,
        amenities_ds_path,
        policies_ds_path,
        flights_blob_path,
        tickets_blob_path,
        seats_blob_path,
        False,
    )
    await ds.initialize_data(airports, amenities, policies, flights, tickets, seats)

    if ds is None:
        raise TypeError("datastore creation failure")
    yield ds
    await ds.close()


async def test_export_dataset(ds: cloudsql_postgres.Client):
    airports, amenities, policies, flights, tickets, seats = await ds.export_data()

    airports_ds_path = "../data/airport_dataset.csv"
    amenities_ds_path = "../data/amenity_dataset.csv"
    policies_ds_path = "../data/cymbalair_policy.csv"
    flights_ds_path = "../data/flights_dataset.csv"
    tickets_ds_path = "../data/tickets_dataset.csv"
    seats_ds_path = "../data/seats_dataset.csv"

    airports_new_path = "../data/airport_dataset.csv.new"
    amenities_new_path = "../data/amenity_dataset.csv.new"
    policies_new_path = "../data/cymbalair_policy.csv.new"
    flights_new_path = "../data/flights_dataset.csv.new"
    tickets_new_path = "../data/tickets_dataset.csv.new"
    seats_new_path = "../data/seats_dataset.csv.new"

    await ds.export_dataset(
        airports,
        amenities,
        policies,
        flights,
        tickets,
        seats,
        airports_new_path,
        amenities_new_path,
        policies_new_path,
        flights_new_path,
        tickets_new_path,
        seats_new_path,
    )

    diff_airports = compare(
        load_csv(open(airports_ds_path), "id"), load_csv(open(airports_new_path), "id")
    )
    assert diff_airports["added"] == []
    assert diff_airports["removed"] == []
    assert diff_airports["changed"] == []
    assert diff_airports["columns_added"] == []
    assert diff_airports["columns_removed"] == []

    diff_amenities = compare(
        load_csv(open(amenities_ds_path), "id"),
        load_csv(open(amenities_new_path), "id"),
    )
    assert diff_amenities["added"] == []
    assert diff_amenities["removed"] == []
    assert diff_amenities["changed"] == []
    assert diff_amenities["columns_added"] == []
    assert diff_amenities["columns_removed"] == []

    diff_flights = compare(
        load_csv(open(flights_ds_path), "id"), load_csv(open(flights_new_path), "id")
    )
    assert diff_flights["added"] == []
    assert diff_flights["removed"] == []
    assert diff_flights["changed"] == []
    assert diff_flights["columns_added"] == []
    assert diff_flights["columns_removed"] == []

    diff_policies = compare(
        load_csv(open(policies_ds_path), "id"),
        load_csv(open(policies_new_path), "id"),
    )
    assert diff_policies["added"] == []
    assert diff_policies["removed"] == []
    assert diff_policies["changed"] == []
    assert diff_policies["columns_added"] == []
    assert diff_policies["columns_removed"] == []

    diff_tickets = compare(
        load_csv(open(tickets_ds_path), "id"), load_csv(open(tickets_new_path), "id")
    )
    assert diff_tickets["added"] == []
    assert diff_tickets["removed"] == []
    assert diff_tickets["changed"] == []
    assert diff_tickets["columns_added"] == []
    assert diff_tickets["columns_removed"] == []


async def test_get_airport_by_id(ds: cloudsql_postgres.Client):
    res = await ds.get_airport_by_id(1)
    expected = models.Airport(
        id=1,
        iata="MAG",
        name="Madang Airport",
        city="Madang",
        country="Papua New Guinea",
    )
    assert res == expected


@pytest.mark.parametrize(
    "iata",
    [
        pytest.param("SFO", id="upper_case"),
        pytest.param("sfo", id="lower_case"),
    ],
)
async def test_get_airport_by_iata(ds: cloudsql_postgres.Client, iata: str):
    res = await ds.get_airport_by_iata(iata)
    expected = models.Airport(
        id=3270,
        iata="SFO",
        name="San Francisco International Airport",
        city="San Francisco",
        country="United States",
    )
    assert res == expected


search_airports_test_data = [
    pytest.param(
        "Philippines",
        "San jose",
        None,
        [
            models.Airport(
                id=2299,
                iata="SJI",
                name="San Jose Airport",
                city="San Jose",
                country="Philippines",
            ),
            models.Airport(
                id=2313,
                iata="EUQ",
                name="Evelio Javier Airport",
                city="San Jose",
                country="Philippines",
            ),
        ],
        id="country_and_city_only",
    ),
    pytest.param(
        "united states",
        "san francisco",
        None,
        [
            models.Airport(
                id=3270,
                iata="SFO",
                name="San Francisco International Airport",
                city="San Francisco",
                country="United States",
            )
        ],
        id="country_and_name_only",
    ),
    pytest.param(
        None,
        "San Jose",
        "San Jose",
        [
            models.Airport(
                id=2299,
                iata="SJI",
                name="San Jose Airport",
                city="San Jose",
                country="Philippines",
            ),
            models.Airport(
                id=3548,
                iata="SJC",
                name="Norman Y. Mineta San Jose International Airport",
                city="San Jose",
                country="United States",
            ),
        ],
        id="city_and_name_only",
    ),
    pytest.param(
        "Foo",
        "FOO BAR",
        "Foo bar",
        [],
        id="no_results",
    ),
]


@pytest.mark.parametrize("country, city, name, expected", search_airports_test_data)
async def test_search_airports(
    ds: cloudsql_postgres.Client,
    country: str,
    city: str,
    name: str,
    expected: List[models.Airport],
):
    res = await ds.search_airports(country, city, name)
    assert res == expected


async def test_get_amenity(ds: cloudsql_postgres.Client):
    res = await ds.get_amenity(0)
    expected = models.Amenity(
        id=0,
        name="Coffee Shop 732",
        description="Serving American cuisine.",
        location="Near Gate B12",
        terminal="Terminal 3",
        category="restaurant",
        hour="Daily 7:00 am - 10:00 pm",
        sunday_start_hour=None,
        sunday_end_hour=None,
        monday_start_hour=None,
        monday_end_hour=None,
        tuesday_start_hour=None,
        tuesday_end_hour=None,
        wednesday_start_hour=None,
        wednesday_end_hour=None,
        thursday_start_hour=None,
        thursday_end_hour=None,
        friday_start_hour=None,
        friday_end_hour=None,
        saturday_start_hour=None,
        saturday_end_hour=None,
    )
    assert res == expected


amenities_search_test_data = [
    pytest.param(
        # "Where can I get coffee near gate A6?"
        amenities_query_embedding1,
        0.35,
        1,
        "10:00:00",
        "wednesday",
        [
            {
                "name": "Coffee Shop 732",
                "description": "Serving American cuisine.",
                "location": "Near Gate B12",
                "terminal": "Terminal 3",
                "category": "restaurant",
                "hour": "Daily 7:00 am - 10:00 pm",
            }
        ],
        id="search_coffee_shop",
    ),
    pytest.param(
        # "Where can I get coffee near gate A6?"
        amenities_query_embedding1,
        0.35,
        1,
        None,
        None,
        [
            {
                "name": "Coffee Shop 732",
                "description": "Serving American cuisine.",
                "location": "Near Gate B12",
                "terminal": "Terminal 3",
                "category": "restaurant",
                "hour": "Daily 7:00 am - 10:00 pm",
            }
        ],
        id="search_coffee_shop_without_filter",
    ),
    pytest.param(
        # "Where can I look for luxury goods?"
        amenities_query_embedding2,
        0.35,
        2,
        "17:00:00",
        "thursday",
        [
            {
                "name": "Gucci Duty Free",
                "description": "Luxury brand duty-free shop offering designer clothing, accessories, and fragrances.",
                "location": "Gate E9",
                "terminal": "International Terminal A",
                "category": "shop",
                "hour": "Daily 7:00 am-10:00 pm",
            },
            {
                "name": "Dufry Duty Free",
                "description": "Duty-free shop offering a large selection of luxury goods, including perfumes, cosmetics, and liquor.",
                "location": "Gate E2",
                "terminal": "International Terminal A",
                "category": "shop",
                "hour": "Daily 7:00 am-10:00 pm",
            },
        ],
        id="search_luxury_goods",
    ),
    pytest.param(
        # "FOO BAR"
        foobar_query_embedding,
        0.1,
        1,
        "12:00:00",
        "friday",
        [],
        id="no_results",
    ),
]


@pytest.mark.parametrize(
    "query_embedding, similarity_threshold, top_k, open_time, open_day, expected",
    amenities_search_test_data,
)
async def test_amenities_search(
    ds: cloudsql_postgres.Client,
    query_embedding: List[float],
    similarity_threshold: float,
    top_k: int,
    open_time: str,
    open_day: str,
    expected: List[Any],
):
    res = await ds.amenities_search(
        "",
        query_embedding,
        similarity_threshold,
        top_k,
        UIFriendlyLogger(),
        open_time,
        open_day,
    )
    assert res == expected


async def test_get_flight(ds: cloudsql_postgres.Client):
    res = await ds.get_flight(1)
    expected = models.Flight(
        id=1,
        airline="UA",
        flight_number="1158",
        departure_airport="SFO",
        arrival_airport="ORD",
        departure_time=datetime.strptime("2024-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"),
        arrival_time=datetime.strptime("2024-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"),
        departure_gate="C38",
        arrival_gate="D30",
    )
    assert res == expected


search_flights_by_number_test_data = [
    pytest.param(
        "UA",
        "1158",
        [
            models.Flight(
                id=1,
                airline="UA",
                flight_number="1158",
                departure_airport="SFO",
                arrival_airport="ORD",
                departure_time=datetime.strptime(
                    "2024-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2024-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="C38",
                arrival_gate="D30",
            ),
            models.Flight(
                id=55455,
                airline="UA",
                flight_number="1158",
                departure_airport="SFO",
                arrival_airport="JFK",
                departure_time=datetime.strptime(
                    "2024-10-15 05:18:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2024-10-15 08:40:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="B50",
                arrival_gate="E4",
            ),
        ],
        id="successful_airport_search",
    ),
    pytest.param(
        "UU",
        "0000",
        [],
        id="no_results",
    ),
]


@pytest.mark.parametrize(
    "airline, number, expected", search_flights_by_number_test_data
)
async def test_search_flights_by_number(
    ds: cloudsql_postgres.Client,
    airline: str,
    number: str,
    expected: List[models.Flight],
):
    res = await ds.search_flights_by_number(airline, number)
    assert res == expected


search_flights_by_airports_test_data = [
    pytest.param(
        "2024-01-01",
        "SFO",
        "ORD",
        [
            models.Flight(
                id=1,
                airline="UA",
                flight_number="1158",
                departure_airport="SFO",
                arrival_airport="ORD",
                departure_time=datetime.strptime(
                    "2024-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2024-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="C38",
                arrival_gate="D30",
            ),
            models.Flight(
                id=13,
                airline="UA",
                flight_number="616",
                departure_airport="SFO",
                arrival_airport="ORD",
                departure_time=datetime.strptime(
                    "2024-01-01 07:14:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2024-01-01 13:24:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="A11",
                arrival_gate="D8",
            ),
            models.Flight(
                id=25,
                airline="AA",
                flight_number="242",
                departure_airport="SFO",
                arrival_airport="ORD",
                departure_time=datetime.strptime(
                    "2024-01-01 08:18:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2024-01-01 14:26:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="E30",
                arrival_gate="C1",
            ),
            models.Flight(
                id=109,
                airline="UA",
                flight_number="1640",
                departure_airport="SFO",
                arrival_airport="ORD",
                departure_time=datetime.strptime(
                    "2024-01-01 17:01:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2024-01-01 23:02:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="E27",
                arrival_gate="C24",
            ),
            models.Flight(
                id=119,
                airline="AA",
                flight_number="197",
                departure_airport="SFO",
                arrival_airport="ORD",
                departure_time=datetime.strptime(
                    "2024-01-01 17:21:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2024-01-01 23:33:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="D25",
                arrival_gate="E49",
            ),
            models.Flight(
                id=136,
                airline="UA",
                flight_number="1564",
                departure_airport="SFO",
                arrival_airport="ORD",
                departure_time=datetime.strptime(
                    "2024-01-01 19:14:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2024-01-02 01:14:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="E3",
                arrival_gate="C48",
            ),
        ],
        id="successful_airport_search",
    ),
    pytest.param(
        "2024-01-01",
        "FOO",
        "BAR",
        [],
        id="no_results",
    ),
]


@pytest.mark.parametrize(
    "date, departure_airport, arrival_airport, expected",
    search_flights_by_airports_test_data,
)
async def test_search_flights_by_airports(
    ds: cloudsql_postgres.Client,
    date: str,
    departure_airport: str,
    arrival_airport: str,
    expected: List[models.Flight],
):
    res = await ds.search_flights_by_airports(date, departure_airport, arrival_airport)
    assert res == expected


policies_search_test_data = [
    pytest.param(
        # "What is the fee for extra baggage?"
        policies_query_embedding1,
        0.35,
        1,
        [
            "## Baggage\nChecked Baggage: Economy passengers are allowed 2 checked bags. Business class and First class passengers are allowed 4 checked bags. Additional baggage will cost $70 and a $30 fee applies for all checked bags over 50 lbs. Cymbal Air cannot accept checked bags over 100 lbs. We only accept checked bags up to 115 inches in total dimensions (length + width + height), and oversized baggage will cost $30. Checked bags above 160 inches in total dimensions will not be accepted.",
        ],
        id="search_extra_baggage_fee",
    ),
    pytest.param(
        # "Can I change my flight?"
        policies_query_embedding2,
        0.35,
        2,
        [
            "Changes: Changes to tickets are permitted at any time until 60 minutes prior to scheduled departure. There are no fees for changes as long as the new ticket is on Cymbal Air and is at an equal or lower price.  If the new ticket has a higher price, the customer must pay the difference between the new and old fares.  Changes to a non-Cymbal-Air flight include a $100 change fee.",
            "# Cymbal Air: Passenger Policy  \n## Ticket Purchase and Changes\nTypes of Fares: Cymbal Air offers a variety of fares (Economy, Premium Economy, Business Class, and First Class). Fare restrictions, such as change fees and refundability, vary depending on the fare purchased.",
        ],
        id="search_flight_delays",
    ),
    pytest.param(
        # "FOO BAR"
        foobar_query_embedding,
        0.35,
        1,
        [],
        id="no_results",
    ),
]


@pytest.mark.parametrize(
    "query_embedding, similarity_threshold, top_k, expected", policies_search_test_data
)
async def test_policies_search(
    ds: cloudsql_postgres.Client,
    query_embedding: List[float],
    similarity_threshold: float,
    top_k: int,
    expected: List[str],
):
    res = await ds.policies_search(
        "", query_embedding, similarity_threshold, top_k, UIFriendlyLogger()
    )
    assert res == expected
