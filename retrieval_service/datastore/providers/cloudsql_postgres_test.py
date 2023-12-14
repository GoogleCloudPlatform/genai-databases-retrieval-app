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

from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, AsyncGenerator, List

import pytest
import pytest_asyncio

import models

from .. import datastore
from . import cloudsql_postgres
from .test_data import query_embedding1, query_embedding2, query_embedding3
from .utils import get_env_var

pytestmark = [pytest.mark.asyncio(scope="module"), pytest.mark.cloudsql]


@pytest.fixture(scope="module")
def db_user() -> str:
    return get_env_var("DB_USER", "name of a postgres user")


@pytest.fixture(scope="module")
def db_pass() -> str:
    return get_env_var("DB_PASS", "password for the postgres user")


@pytest.fixture(scope="module")
def db_name() -> str:
    return get_env_var("DB_NAME", "name of a postgres database")


@pytest.fixture(scope="module")
def db_project() -> str:
    return get_env_var("DB_PROJECT", "project id for google cloud")


@pytest.fixture(scope="module")
def db_region() -> str:
    return get_env_var("DB_REGION", "region for cloud sql instance")


@pytest.fixture(scope="module")
def db_instance() -> str:
    return get_env_var("DB_INSTANCE", "instance for cloud sql")


@pytest_asyncio.fixture(scope="module")
async def ds(
    db_user: str,
    db_pass: str,
    db_name: str,
    db_project: str,
    db_region: str,
    db_instance: str,
) -> AsyncGenerator[datastore.Client, None]:
    cfg = cloudsql_postgres.Config(
        kind="cloudsql-postgres",
        user=db_user,
        password=db_pass,
        database=db_name,
        project=db_project,
        region=db_region,
        instance=db_instance,
    )
    ds = await datastore.create(cfg)
    if ds is None:
        raise TypeError("datastore creation failure")
    yield ds
    print("after yield")
    await ds.close()
    print("closed database")


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
    res = await ds.get_amenity(1)
    expected = models.Amenity(
        id=1,
        name="24th & Mission Taco House",
        description="Fresh made-to-order Mexican entrees with beer & wine",
        location="Marketplace G (near entrance to G Gates)",
        terminal="Ed Lee International Main Hall",
        category="restaurant",
        hour="Sunday- Saturday 7:00 am-8:00 pm",
    )
    assert res == expected


amenities_search_test_data = [
    pytest.param(
        # "Where can I get coffee near gate A6?"
        query_embedding1,
        0.7,
        1,
        [
            models.Amenity(
                id=27,
                name="Green Beans Coffee",
                description="A third wave coffee concept serving handcrafted coffee creations exclusively for travelers in airports across America. For over 25 years Green Beans Coffee has been roasted in the USA, and loved around with world.",
                location="near the entrance to G Gates",
                terminal="Ed Lee International Main Hall",
                category="restaurant",
                hour="Sunday- Saturday 4:00 am-11:00 pm",
                content=None,
                embedding=None,
            ),
        ],
        id="search_coffee_shop",
    ),
    pytest.param(
        # "Where can I look for luxury goods?"
        query_embedding2,
        0.7,
        2,
        [
            models.Amenity(
                id=100,
                name="Gucci",
                description="Luxury apparel, handbags and accessories-duty free",
                location="Gates, near Gate G2",
                terminal="International Terminal G",
                category="shop",
                hour="Sunday - Saturday 7:00 am-11:00 pm",
                content=None,
                embedding=None,
            ),
            models.Amenity(
                id=84,
                name="Coach",
                description="Luxury handbags, accessories and clothing—duty free.",
                location="Between Gates A5 and A9",
                terminal="International Terminal A",
                category="shop",
                hour="Sunday - Saturday 9:00 am-11:00 pm",
                content=None,
                embedding=None,
            ),
        ],
        id="search_luxury_goods",
    ),
    pytest.param(
        # "FOO BAR"
        query_embedding3,
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
    ds: cloudsql_postgres.Client,
    query_embedding: List[float],
    similarity_threshold: float,
    top_k: int,
    expected: List[models.Amenity],
):
    res = await ds.amenities_search(query_embedding, similarity_threshold, top_k)
    assert res == expected


async def test_get_flight(ds: cloudsql_postgres.Client):
    res = await ds.get_flight(1)
    expected = models.Flight(
        id=1,
        airline="UA",
        flight_number="1158",
        departure_airport="SFO",
        arrival_airport="ORD",
        departure_time=datetime.strptime("2023-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"),
        arrival_time=datetime.strptime("2023-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"),
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
                    "2023-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"
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
                    "2023-10-15 05:18:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-10-15 08:40:00", "%Y-%m-%d %H:%M:%S"
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
        "2023-01-01",
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
                    "2023-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"
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
                    "2023-01-01 07:14:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-01 13:24:00", "%Y-%m-%d %H:%M:%S"
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
                    "2023-01-01 08:18:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-01 14:26:00", "%Y-%m-%d %H:%M:%S"
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
                    "2023-01-01 17:01:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-01 23:02:00", "%Y-%m-%d %H:%M:%S"
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
                    "2023-01-01 17:21:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-01 23:33:00", "%Y-%m-%d %H:%M:%S"
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
                    "2023-01-01 19:14:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-02 01:14:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="E3",
                arrival_gate="C48",
            ),
        ],
        id="successful_airport_search",
    ),
    pytest.param(
        "2023-01-01",
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
