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
from typing import Literal, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

import datastore
import models
from datastore import providers

from . import init_app
from .app import AppConfig
from .helpers import get_env_var


class Config(BaseModel):
    kind: Literal["mock-datastore"]


class MockDatastore(datastore.Client[Config]):
    def kind(cls):
        return "mock-datastore"

    async def create(cls, config: Config) -> "Client":
        return cls

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
    ) -> None:
        return

    async def export_data(
        self,
    ) -> tuple[list[models.Airport], list[models.Amenity], list[models.Flight]]:
        return [], [], []

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        mock_airport = models.Airport(
            id=1,
            iata="FOO",
            name="get_airport_by_id",
            city="BAR",
            country="FOO BAR",
        )
        return mock_airport

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        mock_airport = models.Airport(
            id=1,
            iata="FOO",
            name="get_airport_by_iata",
            city="BAR",
            country="FOO BAR",
        )
        return mock_airport

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        mock_airports = [
            models.Airport(
                id=1,
                iata="FOO",
                name="search_airports",
                city="BAR",
                country="FOO BAR",
            )
        ]
        return mock_airports

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        mock_amenity = models.Amenity(
            id=1,
            name="get_amenity",
            description="FOO",
            location="BAR",
            terminal="FOO BAR",
            category="FEE",
            hour="BAZ",
        )
        return mock_amenity

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[models.Amenity]:
        mock_amenities = [
            models.Amenity(
                id=1,
                name="amenities_search",
                description="FOO",
                location="BAR",
                terminal="FOO BAR",
                category="FEE",
                hour="BAZ",
            ),
            models.Amenity(
                id=2,
                name="amenities_search",
                description="FOO",
                location="BAR",
                terminal="FOO BAR",
                category="FEE",
                hour="BAZ",
            ),
            models.Amenity(
                id=3,
                name="amenities_search",
                description="FOO",
                location="BAR",
                terminal="FOO BAR",
                category="FEE",
                hour="BAZ",
            ),
        ]
        return mock_amenities

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        mock_flight = models.Flight(
            id=1,
            airline="get_flight",
            flight_number="FOOBAR",
            departure_airport="FOO",
            arrival_airport="BAR",
            departure_time=datetime.strptime(
                "2023-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"
            ),
            arrival_time=datetime.strptime("2023-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"),
            departure_gate="BAZ",
            arrival_gate="QUX",
        )
        return mock_flight

    async def search_flights_by_number(
        self,
        airline: str,
        flight_number: str,
    ) -> list[models.Flight]:
        mock_flights = [
            models.Flight(
                id=1,
                airline="search_flights_by_number",
                flight_number="FOOBAR",
                departure_airport="FOO",
                arrival_airport="BAR",
                departure_time=datetime.strptime(
                    "2023-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="BAZ",
                arrival_gate="QUX",
            )
        ]
        return mock_flights

    async def search_flights_by_airports(
        self,
        date,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        mock_flights = [
            models.Flight(
                id=1,
                airline="search_flights_by_airports",
                flight_number="FOOBAR",
                departure_airport="FOO",
                arrival_airport="BAR",
                departure_time=datetime.strptime(
                    "2023-01-01 05:57:00", "%Y-%m-%d %H:%M:%S"
                ),
                arrival_time=datetime.strptime(
                    "2023-01-01 12:13:00", "%Y-%m-%d %H:%M:%S"
                ),
                departure_gate="BAZ",
                arrival_gate="QUX",
            )
        ]
        return mock_flights

    async def close(self):
        return


@pytest.fixture(scope="module")
def app():
    mock_app_config = MagicMock()
    app = init_app(mock_app_config)
    if app is None:
        raise TypeError("app did not initialize")
    return app


@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_hello_world(app):
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}


get_airport_params = [
    pytest.param(
        {
            "id": 1,
        },
        {
            "id": 1,
            "iata": "FOO",
            "name": "get_airport_by_id",
            "city": "BAR",
            "country": "FOO BAR",
        },
        id="id_only",
    ),
    pytest.param(
        {"iata": "sfo"},
        {
            "id": 1,
            "iata": "FOO",
            "name": "get_airport_by_iata",
            "city": "BAR",
            "country": "FOO BAR",
        },
        id="iata_only",
    ),
]


@pytest.mark.parametrize("params, expected", get_airport_params)
@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_get_airport(app, params, expected):
    with TestClient(app) as client:
        response = client.get(
            "/airports",
            params=params,
        )
    assert response.status_code == 200
    output = response.json()
    assert output == expected
    assert models.Airport.model_validate(output)


search_airports_params = [
    pytest.param(
        {
            "country": "United States",
            "city": "san francisco",
            "name": "san francisco",
        },
        [
            {
                "id": 1,
                "iata": "FOO",
                "name": "search_airports",
                "city": "BAR",
                "country": "FOO BAR",
            }
        ],
        id="country_city_and_name",
    ),
    pytest.param(
        {"country": "United States"},
        [
            {
                "id": 1,
                "iata": "FOO",
                "name": "search_airports",
                "city": "BAR",
                "country": "FOO BAR",
            }
        ],
        id="country_only",
    ),
    pytest.param(
        {"city": "san francisco"},
        [
            {
                "id": 1,
                "iata": "FOO",
                "name": "search_airports",
                "city": "BAR",
                "country": "FOO BAR",
            }
        ],
        id="city_only",
    ),
    pytest.param(
        {"name": "san francisco"},
        [
        {
            "id": 1,
            "iata": "FOO",
            "name": "search_airports",
            "city": "BAR",
            "country": "FOO BAR",
        }
        ],
        id="name_only",
    ),
]


@pytest.mark.parametrize("params, expected", search_airports_params)
@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_search_airports(app, params, expected):
    with TestClient(app) as client:
        response = client.get(
            "/airports/search",
            params=params,
        )
    assert response.status_code == 200
    output = response.json()
    assert output == expected
    assert models.Airport.model_validate(output[0])


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({}, id="no_params"),
    ],
)
@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_search_airports_with_bad_params(app, params):
    with TestClient(app) as client:
        response = client.get("/airports/search", params=params)
    assert response.status_code == 422


@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_get_amenity(app):
    with TestClient(app) as client:
        response = client.get(
            "/amenities",
            params={
                "id": 1,
            },
        )
    assert response.status_code == 200
    output = response.json()
    expected = {
        "id": 1,
        "name": "get_amenity",
        "description": "FOO",
        "location": "BAR",
        "terminal": "FOO BAR",
        "category": "FEE",
        "hour": "BAZ",
        "content": None,
        "embedding": None,
    }
    assert output == expected
    assert models.Amenity.model_validate(output)


@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_amenities_search(app):
    with TestClient(app) as client:
        response = client.get(
            "/amenities/search",
            params={
                "query": "A place to get food.",
                "top_k": 3,
            },
        )
    assert response.status_code == 200
    output = response.json()
    expected = [
        {
            "id": 1,
            "name": "amenities_search",
            "description": "FOO",
            "location": "BAR",
            "terminal": "FOO BAR",
            "category": "FEE",
            "hour": "BAZ",
            "content": None,
            "embedding": None,
        },
        {
            "id": 2,
            "name": "amenities_search",
            "description": "FOO",
            "location": "BAR",
            "terminal": "FOO BAR",
            "category": "FEE",
            "hour": "BAZ",
            "content": None,
            "embedding": None,
        },
        {
            "id": 3,
            "name": "amenities_search",
            "description": "FOO",
            "location": "BAR",
            "terminal": "FOO BAR",
            "category": "FEE",
            "hour": "BAZ",
            "content": None,
            "embedding": None,
        },
    ]
    assert len(output) == 3
    assert output == expected
    assert models.Amenity.model_validate(output[0])


@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_get_flight(app):
    with TestClient(app) as client:
        response = client.get(
            "/flights",
            params={"flight_id": 1935},
        )
    assert response.status_code == 200
    output = response.json()
    expected = {
        "id": 1,
        "airline": "get_flight",
        "flight_number": "FOOBAR",
        "departure_airport": "FOO",
        "arrival_airport": "BAR",
        "departure_time": "2023-01-01T05:57:00",
        "arrival_time": "2023-01-01T12:13:00",
        "departure_gate": "BAZ",
        "arrival_gate": "QUX",
    }
    assert output == expected
    assert models.Flight.model_validate(output)


search_flights_params = [
    pytest.param(
        {
            "departure_airport": "LAX",
            "arrival_airport": "SFO",
            "date": "2023-11-01",
        },
        [
            {
                "id": 1,
                "airline": "search_flights_by_airports",
                "flight_number": "FOOBAR",
                "departure_airport": "FOO",
                "arrival_airport": "BAR",
                "departure_time": "2023-01-01T05:57:00",
                "arrival_time": "2023-01-01T12:13:00",
                "departure_gate": "BAZ",
                "arrival_gate": "QUX",
            }
        ],
        id="departure_and_arrival_airport",
    ),
    pytest.param(
        {"arrival_airport": "SFO", "date": "2023-11-01"},
        [
            {
                "id": 1,
                "airline": "search_flights_by_airports",
                "flight_number": "FOOBAR",
                "departure_airport": "FOO",
                "arrival_airport": "BAR",
                "departure_time": "2023-01-01T05:57:00",
                "arrival_time": "2023-01-01T12:13:00",
                "departure_gate": "BAZ",
                "arrival_gate": "QUX",
            }
        ],
        id="arrival_airport_only",
    ),
    pytest.param(
        {"departure_airport": "EWR", "date": "2023-11-01"},
        [
            {
                "id": 1,
                "airline": "search_flights_by_airports",
                "flight_number": "FOOBAR",
                "departure_airport": "FOO",
                "arrival_airport": "BAR",
                "departure_time": "2023-01-01T05:57:00",
                "arrival_time": "2023-01-01T12:13:00",
                "departure_gate": "BAZ",
                "arrival_gate": "QUX",
            }
        ],
        id="departure_airport_only",
    ),
    pytest.param(
        {"airline": "DL", "flight_number": "1106"},
        [
            {
                "id": 1,
                "airline": "search_flights_by_number",
                "flight_number": "FOOBAR",
                "departure_airport": "FOO",
                "arrival_airport": "BAR",
                "departure_time": "2023-01-01T05:57:00",
                "arrival_time": "2023-01-01T12:13:00",
                "departure_gate": "BAZ",
                "arrival_gate": "QUX",
            }
        ],
        id="flight_number",
    ),
]


@pytest.mark.parametrize("params, expected", search_flights_params)
@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_search_flights(app, params, expected):
    with TestClient(app) as client:
        response = client.get("/flights/search", params=params)
    assert response.status_code == 200
    output = response.json()
    assert output == expected
    assert models.Flight.model_validate(output[0])


search_flights_bad_params = [
    pytest.param(
        {
            "departure_airport": "LAX",
            "arrival_airport": "SFO",
        },
        id="departure_and_arrival_airport",
    ),
    pytest.param(
        {"arrival_airport": "SFO"},
        id="arrival_airport_only",
    ),
    pytest.param(
        {"departure_airport": "EWR"},
        id="departure_airport_only",
    ),
    pytest.param(
        {"flight_number": "1106"},
        id="flight_number_only",
    ),
    pytest.param(
        {"airline": "DL"},
        id="airline_only",
    ),
]


@pytest.mark.parametrize("params", search_flights_bad_params)
@patch.object(datastore, "create", AsyncMock(return_value=MockDatastore()))
def test_search_flights_with_bad_params(app, params):
    with TestClient(app) as client:
        response = client.get("/flights/search", params=params)
    assert response.status_code == 422
