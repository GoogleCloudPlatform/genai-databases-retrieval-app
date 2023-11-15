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
from typing import Dict

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

import firebase_admin  # type: ignore
import models

from . import firestore as firestore_provider


class MockDocument(Dict):
    """
    Mock firestore document.
    """

    id: int
    content: Dict

    def __init(self, id, content):
        self.id = id
        self.content = content

    def to_dict(self):
        return self.content


class MockCollection(Dict):
    """
    Mock firestore collection.
    """

    collection_name: str
    documents = Dict[str, MockDocument]

    def __init(self, collection_name: str):
        self.collection_name = collection_name

    def where(self, filter: FieldFilter):
        return self.documents

    def select(self, *args):
        return self.documents


class MockFirestoreClient(firestore.AsyncClient):
    """
    Mock firestore client.
    """

    collections: Dict[str, MockCollection]

    def __init(self):
        self.collections = {}

    def collection(self, collection_name: str):
        return self.collections[collection_name]


async def mock_client(mock_firestore_client: MockFirestoreClient) -> firestore.Client:
    return firestore_provider.Client(mock_firestore_client)


async def test_get_airport_by_id():
    fake_id = 1
    mock_document = MockDocument(
        fake_id,
        {
            "iata": "Fake iata",
            "name": "Fake name",
            "city": "Fake city",
            "country": "Fake country",
        },
    )
    mock_collection = MockCollection("airports")
    mock_collection.documents[fake_id, mock_document]
    mock_firestore_client = MockFirestoreClient()
    mock_firestore_client.collection["airports"] = mock_collection

    mock_client = await mock_client(mock_firestore_client)
    res = await mock_client.get_airport_by_id(fake_id)
    expected_res = models.Airport(
        id=fake_id,
        iata="Fake iata",
        name="Fake name",
        city="Fake city",
        country="Fake country",
    )
    assert res == expected_res


async def test_get_airport_by_iata():
    fake_id = 1
    fake_iata = "Fake iata"
    mock_document = MockDocument(
        fake_id,
        {
            "iata": fake_iata,
            "name": "Fake name",
            "city": "Fake city",
            "country": "Fake country",
        },
    )
    mock_collection = MockCollection("airports")
    mock_collection.documents[fake_id, mock_document]
    mock_firestore_client = MockFirestoreClient()
    mock_firestore_client.collection["airports"] = mock_collection

    mock_client = await mock_client(mock_firestore_client)
    res = await mock_client.get_airport_by_iata(fake_iata)
    expected_res = models.Airport(
        id=fake_id,
        iata=fake_iata,
        name="Fake name",
        city="Fake city",
        country="Fake country",
    )
    assert res == expected_res


async def test_search_airports():
    fake_id = 3
    fake_name = "Fake name"
    fake_country = "Fake country"
    fake_city = "Fake city"
    mock_document = MockDocument(
        fake_id,
        {
            "iata": "Fake iata",
            "name": fake_name,
            "city": fake_city,
            "country": fake_country,
        },
    )
    mock_collection = MockCollection("airports")
    mock_collection.documents[fake_id, mock_document]
    mock_firestore_client = MockFirestoreClient()
    mock_firestore_client.collection["airports"] = mock_collection

    mock_client = await mock_client(mock_firestore_client)
    res = await mock_client.search_airports(fake_country, fake_city, fake_name)
    expected_res = [
        models.Airport(
            id=fake_id,
            iata="Fake iata",
            name=fake_name,
            city=fake_city,
            country=fake_country,
        )
    ]

    assert res == expected_res


async def test_get_amenity():
    fake_id = 2
    mock_document = MockDocument(
        fake_id,
        {
            "name",
            "Fake name",
            "description",
            "Fake description",
            "location",
            "Fake location",
            "terminal",
            "Fake terminal",
            "category",
            "Fake category",
            "hour",
            "Fake hour",
        },
    )
    mock_collection = MockCollection("amenities")
    mock_collection.documents[fake_id, mock_document]
    mock_firestore_client = MockFirestoreClient()
    mock_firestore_client.collection["amenities"] = mock_collection

    mock_client = await mock_client(mock_firestore_client)
    res = await mock_client.get_amenity(fake_id)
    expected_res = models.Amenity(
        id=fake_id,
        name="Fake name",
        description="Fake description",
        location="Fake location",
        terminal="Fake terminal",
        category="Fake category",
        hour="Fake hour",
    )
    assert res == expected_res


async def test_amenities_search():
    fake_id = 3
    mock_document = MockDocument(
        fake_id,
        {
            "name": "Fake name",
            "description": "Fake description",
            "location": "Fake location",
            "terminal": "Fake terminal",
            "category": "Fake category",
            "hour": "Fake hour",
        },
    )
    mock_collection = MockCollection("amenities")
    mock_collection.documents[fake_id, mock_document]
    mock_firestore_client = MockFirestoreClient()
    mock_firestore_client.collection["amenities"] = mock_collection

    mock_client = await mock_client(mock_firestore_client)
    res = await mock_client.amenities_search(1, 0.7, 1)
    expected_res = [
        models.Amenity(
            id=fake_id,
            name="Fake name",
            description="Fake description",
            location="Fake location",
            terminal="Fake terminal",
            category="Fake category",
            hour="Fake hour",
        )
    ]
    assert res == expected_res


async def test_get_flight():
    fake_id = 4
    fake_datetime = datetime.datetime(2023, 11, 14, 12, 30, 45)
    mock_document = MockDocument(
        fake_id,
        {
            "airline": "Fake airline",
            "flight_number": "Fake flight number",
            "departure_airport": "Fake departure airport",
            "arrival_airport": "Fake arrival airport",
            "departure_time": fake_datetime,
            "arrival_time": fake_datetime,
            "departure_gate": "fake departure gate",
            "arrival_gate": "fake arrival gate",
        },
    )
    mock_collection = MockCollection("flights")
    mock_collection.documents[fake_id, mock_document]
    mock_firestore_client = MockFirestoreClient()
    mock_firestore_client.collection["flights"] = mock_collection

    mock_client = await mock_client(mock_firestore_client)
    res = await mock_client.get_flight(fake_id)
    expected_res = models.Flight(
        id=fake_id,
        airline="Fake airline",
        flight_number="Fake flight number",
        departure_airport="Fake departure airport",
        arrival_airport="Fake arrival airport",
        departure_time=fake_datetime,
        arrival_time=fake_datetime,
        departure_gate="fake departure gate",
        arrival_gate="fake arrival gate",
    )
    assert res == expected_res


async def test_search_flights_by_airports():
    fake_id = 5
    fake_date = "2023-11-14"
    fake_datetime = datetime.datetime(2023, 11, 14, 12, 30, 45)
    mock_document = MockDocument(
        fake_id,
        {
            "airline": "Fake airline",
            "flight_number": "Fake flight number",
            "departure_airport": "Fake departure airport",
            "arrival_airport": "Fake arrival airport",
            "departure_time": fake_datetime,
            "arrival_time": fake_datetime,
            "departure_gate": "fake departure gate",
            "arrival_gate": "fake arrival gate",
        },
    )
    mock_collection = MockCollection("flights")
    mock_collection.documents[fake_id, mock_document]
    mock_firestore_client = MockFirestoreClient()
    mock_firestore_client.collection["flights"] = mock_collection

    mock_client = await mock_client(mock_firestore_client)
    res = await mock_client.search_flights_by_airport(
        fake_date, "Fake departure airport", "Fake arrival airport"
    )
    expected_res = [
        models.Flight(
            id=fake_id,
            airline="Fake airline",
            flight_number="Fake flight number",
            departure_airport="Fake departure airport",
            arrival_airport="Fake arrival airport",
            departure_time=fake_datetime,
            arrival_time=fake_datetime,
            departure_gate="fake departure gate",
            arrival_gate="fake arrival gate",
        )
    ]
    assert res == expected_res
