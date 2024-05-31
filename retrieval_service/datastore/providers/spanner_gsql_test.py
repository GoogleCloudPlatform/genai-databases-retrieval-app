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

from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, AsyncGenerator, List, Optional

import pytest
import pytest_asyncio
from csv_diff import compare, load_csv  # type: ignore
from google.cloud import spanner  # type: ignore
from google.cloud.spanner_v1 import JsonObject, param_types
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.instance import Instance
from google.oauth2 import service_account  # type: ignore

import models

from .. import datastore
from . import spanner_gsql
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
def db_project() -> str:
    return get_env_var("DB_PROJECT", "Google Cloud Project")


@pytest.fixture(scope="module")
def db_instance() -> str:
    return get_env_var("DB_INSTANCE", "Spanner Instance")


@pytest.fixture(scope="module")
def db_name() -> str:
    return get_env_var("DB_NAME", "Spanner Database")


@pytest.fixture(scope="module")
def service_accounts_file_path() -> str:
    return get_env_var(
        "SERVICE_ACCOUNT_KEY_FILE", "Service account with permission to spanner"
    )


@pytest.fixture(scope="module")
async def create_db(
    db_project: str, db_instance: str, db_name: str, service_accounts_file_path: str
) -> AsyncGenerator[str, None]:
    credentials = service_account.Credentials.from_service_account_file(
        service_accounts_file_path
    )

    client = spanner.Client(project=db_project, credentials=credentials)
    instance = client.instance(db_instance)

    database = instance.database(db_name)

    database.create()

    yield db_name

    database.drop()
    client.close()


@pytest_asyncio.fixture(scope="module")
async def ds(
    create_db: AsyncGenerator[str, None],
    db_project: str,
    db_instance: str,
    service_accounts_file_path: str,
) -> AsyncGenerator[datastore.Client, None]:
    db_name = await create_db.__anext__()
    cfg = spanner_gsql.Config(
        kind="spanner-gsql",
        project=db_project,
        instance=db_instance,
        database=db_name,
        service_account_key_file=service_accounts_file_path,
    )

    ds = await datastore.create(cfg)

    airports_ds_path = "../../../data/airport_dataset.csv"
    amenities_ds_path = "../../../data/amenity_dataset.csv"
    flights_ds_path = "../../../data/flights_dataset.csv"
    policies_ds_path = "../../../data/cymbalair_policy.csv"
    airports, amenities, flights, policies = await ds.load_dataset(
        airports_ds_path,
        amenities_ds_path,
        flights_ds_path,
        policies_ds_path,
    )
    await ds.initialize_data(airports, amenities, flights, policies)

    if ds is None:
        raise TypeError("datastore creation failure")

    yield ds

    await ds.close()


def check_file_diff(file_diff):
    assert file_diff["added"] == []
    assert file_diff["removed"] == []
    assert file_diff["changed"] == []
    assert file_diff["columns_added"] == []
    assert file_diff["columns_removed"] == []


async def test_export_dataset(ds: spanner_gsql.Client):
    airports, amenities, flights, policies = await ds.export_data()

    airports_ds_path = "../../../data/airport_dataset.csv"
    amenities_ds_path = "../../../data/amenity_dataset.csv"
    flights_ds_path = "../../../data/flights_dataset.csv"
    policies_ds_path = "../../../data/cymbalair_policy.csv"

    airports_new_path = "../../../data/airport_dataset.csv.new"
    amenities_new_path = "../../../data/amenity_dataset.csv.new"
    flights_new_path = "../../../data/flights_dataset.csv.new"
    policies_new_path = "../../../data/cymbalair_policy.csv.new"

    await ds.export_dataset(
        airports,
        amenities,
        flights,
        policies,
        airports_new_path,
        amenities_new_path,
        flights_new_path,
        policies_new_path,
    )

    diff_airports = compare(
        load_csv(open(airports_ds_path), "id"), load_csv(open(airports_new_path), "id")
    )
    check_file_diff(diff_airports)

    diff_amenities = compare(
        load_csv(open(amenities_ds_path), "id"),
        load_csv(open(amenities_new_path), "id"),
    )
    check_file_diff(diff_amenities)

    diff_flights = compare(
        load_csv(open(flights_ds_path), "id"), load_csv(open(flights_new_path), "id")
    )
    check_file_diff(diff_flights)

    diff_policies = compare(
        load_csv(open(policies_ds_path), "id"),
        load_csv(open(policies_new_path), "id"),
    )
    check_file_diff(diff_policies)


async def test_get_airport_by_id(ds: spanner_gsql.Client):
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
async def test_get_airport_by_iata(ds: spanner_gsql.Client, iata: str):
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
    ds: spanner_gsql.Client,
    country: str,
    city: str,
    name: str,
    expected: List[models.Airport],
):
    res = await ds.search_airports(country, city, name)
    assert res == expected


async def test_get_amenity(ds: spanner_gsql.Client):
    res: Optional[models.Amenity] = await ds.get_amenity(0)
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

    assert res is not None
    assert res.name == expected.name
    assert res.description == expected.description
    assert res.location == expected.location
    assert res.terminal == expected.terminal
    assert res.category == expected.category
    assert res.hour == expected.hour


amenities_search_test_data = [
    pytest.param(
        # "Where can I get coffee near gate A6?"
        amenities_query_embedding1,
        0.65,
        1,
        [
            {
                "name": "Coffee Shop 732",
                "description": "Serving American cuisine.",
                "location": "Near Gate B12",
                "terminal": "Terminal 3",
                "category": "restaurant",
                "hour": "Daily 7:00 am - 10:00 pm",
            },
        ],
        id="search_coffee_shop",
    ),
    pytest.param(
        # "Where can I look for luxury goods?"
        amenities_query_embedding2,
        0.65,
        2,
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
        0.9,
        1,
        [],
        id="no_results",
    ),
]


@pytest.mark.parametrize(
    "query_embedding, similarity_threshold, top_k, expected", amenities_search_test_data
)
async def test_amenities_search(
    ds: spanner_gsql.Client,
    query_embedding: List[float],
    similarity_threshold: float,
    top_k: int,
    expected: List[models.Amenity],
):
    res = await ds.amenities_search(query_embedding, similarity_threshold, top_k)
    assert res == expected


async def test_get_flight(ds: spanner_gsql.Client):
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
    ds: spanner_gsql.Client,
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
    ds: spanner_gsql.Client,
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
        0.65,
        1,
        [
            "## Baggage\nChecked Baggage: Economy passengers are allowed 2 checked bags. Business class and First class passengers are allowed 4 checked bags. Additional baggage will cost $70 and a $30 fee applies for all checked bags over 50 lbs. Cymbal Air cannot accept checked bags over 100 lbs. We only accept checked bags up to 115 inches in total dimensions (length + width + height), and oversized baggage will cost $30. Checked bags above 160 inches in total dimensions will not be accepted.",
        ],
        id="search_extra_baggage_fee",
    ),
    pytest.param(
        # "Can I change my flight?"
        policies_query_embedding2,
        0.65,
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
        0.65,
        1,
        [],
        id="no_results",
    ),
]


@pytest.mark.parametrize(
    "query_embedding, similarity_threshold, top_k, expected", policies_search_test_data
)
async def test_policies_search(
    ds: spanner_gsql.Client,
    query_embedding: List[float],
    similarity_threshold: float,
    top_k: int,
    expected: List[models.Policy],
):
    res = await ds.policies_search(query_embedding, similarity_threshold, top_k)
    assert res == expected
