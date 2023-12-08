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

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from typing import Literal, Optional
from pydantic import BaseModel

import models
import datastore
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
        )
        return mock_airport

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        mock_airport = models.Airport(
            id=1,
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
            )
        ]
        return mock_airports

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        mock_amenity = models.Amenity(id=1)
        return mock_amenity

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[models.Amenity]:
        mock_amenities = []
        return mock_amenities

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        mock_flight = models.Flight(id=1)
        return mock_flight

    async def search_flights_by_number(
        self,
        airline: str,
        flight_number: str,
    ) -> list[models.Flight]:
        mock_flights = []
        return mock_flights

    async def search_flights_by_airports(
        self,
        date,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        mock_flights = []
        return mock_flights

    async def close(self):
        return


@pytest.fixture(scope="module")
@patch('datastore.create')
def app(mock_datastore):
    mock_ds = MockDatastore()
    mock_datastore.return_value = mock_ds
    mock_app_config = MagicMock()
    app = init_app(mock_app_config)
    if app is None:
        raise TypeError("app did not initialize")
    return app


def test_hello_world(app):
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {
                "id": 1,
            },
            id="id_only",
        ),
        pytest.param({"iata": "sfo"}, id="iata_only"),
    ],
)
def test_get_airport(app, params):
    with TestClient(app) as client:
        response = client.get(
            "/airports",
            params=params,
        )
    assert response.status_code == 200
    output = response.json()
    assert output
    assert models.Airport.model_validate(output)
