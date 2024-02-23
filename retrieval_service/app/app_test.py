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

from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

import datastore
import models
import pytest
from fastapi.testclient import TestClient

from . import init_app
from .app import AppConfig


@pytest.fixture(scope="module")
def app():
    mock_cfg = MagicMock()
    mock_cfg.clientId = "fake client id"
    app = init_app(mock_cfg)
    if app is None:
        raise TypeError("app did not initialize")
    return app


@patch.object(datastore, "create")
def test_hello_world(m_datastore, app):
    m_datastore = AsyncMock()
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}


get_airport_params = [
    pytest.param(
        "get_airport_by_id",
        {
            "id": 1,
        },
        models.Airport(
            id=1,
            iata="FOO",
            name="get_airport_by_id",
            city="BAR",
            country="FOO BAR",
        ),
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
        "get_airport_by_iata",
        {"iata": "sfo"},
        models.Airport(
            id=1,
            iata="FOO",
            name="get_airport_by_iata",
            city="BAR",
            country="FOO BAR",
        ),
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


@pytest.mark.parametrize(
    "method_name, params, mock_return, expected", get_airport_params
)
@patch.object(datastore, "create")
def test_get_airport(m_datastore, app, method_name, params, mock_return, expected):
    with TestClient(app) as client:
        with patch.object(
            m_datastore.return_value, method_name, AsyncMock(return_value=mock_return)
        ) as mock_method:
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
        "search_airports",
        {
            "country": "United States",
            "city": "san francisco",
            "name": "san francisco",
        },
        [
            models.Airport(
                id=1,
                iata="FOO",
                name="search_airports",
                city="BAR",
                country="FOO BAR",
            )
        ],
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
        "search_airports",
        {"country": "United States"},
        [
            models.Airport(
                id=1,
                iata="FOO",
                name="search_airports",
                city="BAR",
                country="FOO BAR",
            )
        ],
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
        "search_airports",
        {"city": "san francisco"},
        [
            models.Airport(
                id=1,
                iata="FOO",
                name="search_airports",
                city="BAR",
                country="FOO BAR",
            )
        ],
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
        "search_airports",
        {"name": "san francisco"},
        [
            models.Airport(
                id=1,
                iata="FOO",
                name="search_airports",
                city="BAR",
                country="FOO BAR",
            )
        ],
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


@pytest.mark.parametrize(
    "method_name, params, mock_return, expected", search_airports_params
)
@patch.object(datastore, "create")
def test_search_airports(m_datastore, app, method_name, params, mock_return, expected):
    with TestClient(app) as client:
        with patch.object(
            m_datastore.return_value, method_name, AsyncMock(return_value=mock_return)
        ) as mock_method:
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
@patch.object(datastore, "create")
def test_search_airports_with_bad_params(m_datastore, app, params):
    m_datastore = AsyncMock()
    with TestClient(app) as client:
        response = client.get("/airports/search", params=params)
    assert response.status_code == 422


get_amenity_params = [
    pytest.param(
        "get_amenity",
        {"id": 1},
        models.Amenity(
            id=1,
            name="get_amenity",
            description="FOO",
            location="BAR",
            terminal="FOO BAR",
            category="FEE",
            hour="BAZ",
        ),
        {
            "id": 1,
            "name": "get_amenity",
            "description": "FOO",
            "location": "BAR",
            "terminal": "FOO BAR",
            "category": "FEE",
            "hour": "BAZ",
            "sunday_start_hour": None,
            "sunday_end_hour": None,
            "monday_start_hour": None,
            "monday_end_hour": None,
            "tuesday_start_hour": None,
            "tuesday_end_hour": None,
            "wednesday_start_hour": None,
            "wednesday_end_hour": None,
            "thursday_start_hour": None,
            "thursday_end_hour": None,
            "friday_start_hour": None,
            "friday_end_hour": None,
            "saturday_start_hour": None,
            "saturday_end_hour": None,
            "content": None,
            "embedding": None,
        },
    )
]


@pytest.mark.parametrize(
    "method_name, params, mock_return, expected", get_amenity_params
)
@patch.object(datastore, "create")
def test_get_amenity(m_datastore, app, method_name, params, mock_return, expected):
    with TestClient(app) as client:
        with patch.object(
            m_datastore.return_value, method_name, AsyncMock(return_value=mock_return)
        ) as mock_method:
            response = client.get(
                "/amenities",
                params={
                    "id": 1,
                },
            )
    assert response.status_code == 200
    output = response.json()
    assert output == expected
    assert models.Amenity.model_validate(output)


amenities_search_params = [
    pytest.param(
        "amenities_search",
        {
            "query": "A place to get food.",
            "top_k": 2,
        },
        [
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
        ],
        [
            {
                "id": 1,
                "name": "amenities_search",
                "description": "FOO",
                "location": "BAR",
                "terminal": "FOO BAR",
                "category": "FEE",
                "hour": "BAZ",
                "sunday_start_hour": None,
                "sunday_end_hour": None,
                "monday_start_hour": None,
                "monday_end_hour": None,
                "tuesday_start_hour": None,
                "tuesday_end_hour": None,
                "wednesday_start_hour": None,
                "wednesday_end_hour": None,
                "thursday_start_hour": None,
                "thursday_end_hour": None,
                "friday_start_hour": None,
                "friday_end_hour": None,
                "saturday_start_hour": None,
                "saturday_end_hour": None,
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
                "sunday_start_hour": None,
                "sunday_end_hour": None,
                "monday_start_hour": None,
                "monday_end_hour": None,
                "tuesday_start_hour": None,
                "tuesday_end_hour": None,
                "wednesday_start_hour": None,
                "wednesday_end_hour": None,
                "thursday_start_hour": None,
                "thursday_end_hour": None,
                "friday_start_hour": None,
                "friday_end_hour": None,
                "saturday_start_hour": None,
                "saturday_end_hour": None,
                "content": None,
                "embedding": None,
            },
        ],
    )
]


@pytest.mark.parametrize(
    "method_name, params, mock_return, expected", amenities_search_params
)
@patch.object(datastore, "create")
def test_amenities_search(m_datastore, app, method_name, params, mock_return, expected):
    with TestClient(app) as client:
        with patch.object(
            m_datastore.return_value, method_name, AsyncMock(return_value=mock_return)
        ) as mock_method:
            response = client.get(
                "/amenities/search",
                params=params,
            )
    assert response.status_code == 200
    output = response.json()
    assert len(output) == params["top_k"]
    assert output == expected
    assert models.Amenity.model_validate(output[0])


get_flight_params = [
    pytest.param(
        "get_flight",
        {"flight_id": 1935},
        models.Flight(
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
        ),
        {
            "id": 1,
            "airline": "get_flight",
            "flight_number": "FOOBAR",
            "departure_airport": "FOO",
            "arrival_airport": "BAR",
            "departure_time": "2023-01-01T05:57:00",
            "arrival_time": "2023-01-01T12:13:00",
            "departure_gate": "BAZ",
            "arrival_gate": "QUX",
        },
        id="successful",
    )
]


@pytest.mark.parametrize(
    "method_name, params, mock_return, expected", get_flight_params
)
@patch.object(datastore, "create")
def test_get_flight(m_datastore, app, method_name, params, mock_return, expected):
    with TestClient(app) as client:
        with patch.object(
            m_datastore.return_value, method_name, AsyncMock(return_value=mock_return)
        ) as mock_method:
            response = client.get(
                "/flights",
                params=params,
            )
    assert response.status_code == 200
    output = response.json()
    assert output == expected
    assert models.Flight.model_validate(output)


search_flights_params = [
    pytest.param(
        "search_flights_by_airports",
        {
            "departure_airport": "LAX",
            "arrival_airport": "SFO",
            "date": "2023-11-01",
        },
        [
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
        ],
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
        "search_flights_by_airports",
        {"arrival_airport": "SFO", "date": "2023-11-01"},
        [
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
        ],
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
        "search_flights_by_airports",
        {"departure_airport": "EWR", "date": "2023-11-01"},
        [
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
        ],
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
        "search_flights_by_number",
        {"airline": "DL", "flight_number": "1106"},
        [
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
        ],
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
        id="airline_and_flight_number",
    ),
]


@pytest.mark.parametrize(
    "method_name, params, mock_return, expected", search_flights_params
)
@patch.object(datastore, "create")
def test_search_flights(m_datastore, app, method_name, params, mock_return, expected):
    with TestClient(app) as client:
        with patch.object(
            m_datastore.return_value, method_name, AsyncMock(return_value=mock_return)
        ) as mock_method:
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
@patch.object(datastore, "create")
def test_search_flights_with_bad_params(m_datastore, app, params):
    m_datastore = AsyncMock()
    with TestClient(app) as client:
        response = client.get("/flights/search", params=params)
    assert response.status_code == 422
