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
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from google.oauth2 import id_token

import datastore
import models

from . import init_app


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
            m_datastore.return_value,
            method_name,
            AsyncMock(return_value=(mock_return, None)),
        ) as mock_method:
            response = client.get(
                "/airports",
                params=params,
            )
    assert response.status_code == 200
    res = response.json()
    output = res["results"]
    assert output == expected
    assert models.Airport.model_validate(output)


@patch.object(datastore, "create")
def test_get_airport_missing_params(m_datastore, app):
    m_datastore = AsyncMock()
    with TestClient(app) as client:
        response = client.get("/airports")
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "Request requires query params: airport id or iata"
        )


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
            m_datastore.return_value,
            method_name,
            AsyncMock(return_value=(mock_return, None)),
        ) as mock_method:
            response = client.get(
                "/airports/search",
                params=params,
            )
    assert response.status_code == 200
    res = response.json()
    output = res["results"]
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
            m_datastore.return_value,
            method_name,
            AsyncMock(return_value=(mock_return, None)),
        ) as mock_method:
            response = client.get(
                "/amenities",
                params={
                    "id": 1,
                },
            )
    assert response.status_code == 200
    res = response.json()
    output = res["results"]
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
            m_datastore.return_value,
            method_name,
            AsyncMock(return_value=(mock_return, None)),
        ) as mock_method:
            response = client.get(
                "/amenities/search",
                params=params,
            )
    assert response.status_code == 200
    res = response.json()
    output = res["results"]
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
            m_datastore.return_value,
            method_name,
            AsyncMock(return_value=(mock_return, None)),
        ) as mock_method:
            response = client.get(
                "/flights",
                params=params,
            )
    assert response.status_code == 200
    res = response.json()
    output = res["results"]
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
            m_datastore.return_value,
            method_name,
            AsyncMock(return_value=(mock_return, None)),
        ) as mock_method:
            response = client.get("/flights/search", params=params)
    assert response.status_code == 200
    res = response.json()
    output = res["results"]
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


@patch.object(datastore, "create")
def test_search_flights_missing_params(m_datastore, app):
    m_datastore = AsyncMock()
    with TestClient(app) as client:
        response = client.get("/flights/search")
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "Request requires query params: arrival_airport, departure_airport, date, or both airline and flight_number"
        )


validate_ticket_params = [
    pytest.param(
        "validate_ticket",
        {
            "airline": "CY",
            "flight_number": "888",
            "departure_airport": "LAX",
            "departure_time": "2024-01-01 08:08:08",
        },
        [
            models.Flight(
                id=1,
                airline="validate_ticket",
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
                "airline": "validate_ticket",
                "flight_number": "FOOBAR",
                "departure_airport": "FOO",
                "arrival_airport": "BAR",
                "departure_time": "2023-01-01T05:57:00",
                "arrival_time": "2023-01-01T12:13:00",
                "departure_gate": "BAZ",
                "arrival_gate": "QUX",
            }
        ],
        id="validate_ticket",
    ),
]


@pytest.mark.parametrize(
    "method_name, params, mock_return, expected", validate_ticket_params
)
@patch.object(datastore, "create")
def test_validate_ticket(m_datastore, app, method_name, params, mock_return, expected):
    with TestClient(app) as client:
        with patch.object(
            m_datastore.return_value,
            method_name,
            AsyncMock(return_value=(mock_return, None)),
        ) as mock_method:
            response = client.get("/tickets/validate", params=params)
    assert response.status_code == 200
    res = response.json()
    output = res["results"]
    assert output == expected
    assert models.Flight.model_validate(output[0])


policies_search_params = [
    pytest.param(
        "policies_search",
        {
            "query": "Additional fee for flight changes.",
            "top_k": 1,
        },
        [
            models.Policy(
                id=1,
                content="foo bar",
            ),
        ],
        [
            {
                "id": 1,
                "content": "foo bar",
                "embedding": None,
            },
        ],
    )
]


@pytest.mark.parametrize(
    "method_name, params, mock_return, expected", policies_search_params
)
@patch.object(datastore, "create")
def test_policies_search(m_datastore, app, method_name, params, mock_return, expected):
    with TestClient(app) as client:
        with patch.object(
            m_datastore.return_value,
            method_name,
            AsyncMock(return_value=(mock_return, None)),
        ) as mock_method:
            response = client.get(
                "/policies/search",
                params=params,
            )
    assert response.status_code == 200
    res = response.json()
    output = res["results"]
    assert len(output) == params["top_k"]
    assert output == expected
    assert models.Policy.model_validate(output[0])


@patch.object(id_token, "verify_oauth2_token")
@patch.object(datastore, "create")
def test_insert_ticket_missing_user_info(m_datastore, m_verify_oauth2_token, app):
    m_datastore = AsyncMock()
    m_verify_oauth2_token.side_effect = ValueError("invalid token")
    with TestClient(app) as client:
        response = client.post(
            "/tickets/insert",
            json={
                "airline": "CY",
                "flight_number": "888",
                "departure_airport": "LAX",
                "arrival_airport": "JFK",
                "departure_time": "2024-01-01 08:08:08",
                "arrival_time": "2024-01-01 08:08:08",
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"] == [
            {
                "type": "missing",
                "loc": ["query", "airline"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["query", "flight_number"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["query", "departure_airport"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["query", "arrival_airport"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["query", "departure_time"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["query", "arrival_time"],
                "msg": "Field required",
                "input": None,
            },
        ]


@patch.object(id_token, "verify_oauth2_token")
@patch.object(datastore, "create")
def test_list_tickets_missing_user_info(m_datastore, m_verify_oauth2_token, app):
    m_datastore = AsyncMock()
    m_verify_oauth2_token.side_effect = ValueError("invalid token")
    with TestClient(app) as client:
        response = client.get(
            "/tickets/list", headers={"User-Id-Token": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "User login required for data insertion"
