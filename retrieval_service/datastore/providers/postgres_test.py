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
from collections import OrderedDict
from ipaddress import IPv4Address
from typing import Dict, cast

import pytest
import pytest_asyncio
from langchain.embeddings import VertexAIEmbeddings

import models

from .. import datastore
from . import postgres
from .helpers import get_env_var

DB_USER = get_env_var("DB_USER", "name of a postgres user")
DB_PASS = get_env_var("DB_PASS", "password for the postgres user")
DB_NAME = get_env_var("DB_NAME", "name of a postgres database")
DB_HOST = get_env_var("DB_HOST", "ip address of a postgres database")


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def ds():
    cfg = postgres.Config(
        kind="postgres",
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        host=IPv4Address(DB_HOST),
    )
    ds = await datastore.create(cfg)
    if ds is None:
        raise TypeError("datastore creation failure")
    else:
        print("done")
    yield ds
    await ds.close()


@pytest.mark.asyncio
async def test_get_airport_by_id(ds):
    res = await ds.get_airport_by_id(1)
    expected = models.Airport(
        id=1,
        iata="MAG",
        name="Madang Airport",
        city="Madang",
        country="Papua New Guinea",
    )
    assert res == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "iata",
    [
        pytest.param("SFO", id="upper_case"),
        pytest.param("sfo", id="lower_case"),
    ],
)
async def test_get_airport_by_iata(ds, iata):
    res = await ds.get_airport_by_iata(iata)
    expected = models.Airport(
        id=3270,
        iata="SFO",
        name="San Francisco International Airport",
        city="San Francisco",
        country="United States",
    )
    assert res == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "country, city, name, expected",
    [
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
    ],
)
async def test_search_airports(ds, country, city, name, expected):
    res = await ds.search_airports(country, city, name)
    assert res == expected


@pytest.mark.asyncio
async def test_get_amenity(ds):
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query, similarity_threshold, top_k, expected",
    [
        pytest.param(
            "Where can I get coffee near gate A6?",
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
            "Where can I look for luxury goods?",
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
            "FOO BAR",
            0.9,
            1,
            [],
            id="no_results",
        ),
    ],
)
async def test_amenities_search(ds, query, similarity_threshold, top_k, expected):
    embed_service = VertexAIEmbeddings()
    query_embedding = embed_service.embed_query(query)
    res = await ds.amenities_search(query_embedding, similarity_threshold, top_k)
    assert res == expected


@pytest.mark.asyncio
async def test_get_flight(ds):
    res = await ds.get_flight(1)
    expected = models.Flight(
        id=1,
        airline="UA",
        flight_number="1158",
        departure_airport="SFO",
        arrival_airport="ORD",
        departure_time="2023-01-01 05:57:00",
        arrival_time="2023-01-01 12:13:00",
        departure_gate="C38",
        arrival_gate="D30",
    )
    assert res == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "airline, number, expected",
    [
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
                    departure_time="2023-01-01 05:57:00",
                    arrival_time="2023-01-01 12:13:00",
                    departure_gate="C38",
                    arrival_gate="D30",
                ),
                models.Flight(
                    id=55455,
                    airline="UA",
                    flight_number="1158",
                    departure_airport="SFO",
                    arrival_airport="JFK",
                    departure_time="2023-10-15 05:18:00",
                    arrival_time="2023-10-15 08:40:00",
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
    ],
)
async def test_search_flights_by_number(ds, airline, number, expected):
    res = await ds.search_flights_by_number(airline, number)
    assert res == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date, departure_airport, arrival_airport, expected",
    [
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
                    departure_time="2023-01-01 05:57:00",
                    arrival_time="2023-01-01 12:13:00",
                    departure_gate="C38",
                    arrival_gate="D30",
                ),
                models.Flight(
                    id=13,
                    airline="UA",
                    flight_number="616",
                    departure_airport="SFO",
                    arrival_airport="ORD",
                    departure_time="2023-01-01 07:14:00",
                    arrival_time="2023-01-01 13:24:00",
                    departure_gate="A11",
                    arrival_gate="D8",
                ),
                models.Flight(
                    id=25,
                    airline="AA",
                    flight_number="242",
                    departure_airport="SFO",
                    arrival_airport="ORD",
                    departure_time="2023-01-01 08:18:00",
                    arrival_time="2023-01-01 14:26:00",
                    departure_gate="E30",
                    arrival_gate="C1",
                ),
                models.Flight(
                    id=109,
                    airline="UA",
                    flight_number="1640",
                    departure_airport="SFO",
                    arrival_airport="ORD",
                    departure_time="2023-01-01 17:01:00",
                    arrival_time="2023-01-01 23:02:00",
                    departure_gate="E27",
                    arrival_gate="C24",
                ),
                models.Flight(
                    id=119,
                    airline="AA",
                    flight_number="197",
                    departure_airport="SFO",
                    arrival_airport="ORD",
                    departure_time="2023-01-01 17:21:00",
                    arrival_time="2023-01-01 23:33:00",
                    departure_gate="D25",
                    arrival_gate="E49",
                ),
                models.Flight(
                    id=136,
                    airline="UA",
                    flight_number="1564",
                    departure_airport="SFO",
                    arrival_airport="ORD",
                    departure_time="2023-01-01 19:14:00",
                    arrival_time="2023-01-02 01:14:00",
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
    ],
)
async def test_search_flights_by_airports(
    ds, date, departure_airport, arrival_airport, expected
):
    res = await ds.search_flights_by_airports(date, departure_airport, arrival_airport)
    assert res == expected
