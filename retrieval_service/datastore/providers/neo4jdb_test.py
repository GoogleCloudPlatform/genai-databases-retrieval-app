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

from typing import AsyncGenerator

import pytest
import pytest_asyncio

import models

from .. import datastore
from . import neo4jdb
from .utils import get_env_var

pytestmark = pytest.mark.asyncio(scope="module")


@pytest.fixture(scope="module")
def db_uri() -> str:
    return str(get_env_var("DB_URI", "neo4 uri"))


@pytest.fixture(scope="module")
def db_user() -> str:
    return str(get_env_var("DB_USER", "neo4 user"))


@pytest.fixture(scope="module")
def db_password() -> str:
    return str(get_env_var("DB_PASSWORD", "neo4 password"))


@pytest.fixture(scope="module")
def db_auth(db_user, db_password) -> tuple:
    return (db_user, db_password)


@pytest_asyncio.fixture(scope="module")
async def data_set(
    db_uri: str,
    db_auth: tuple,
) -> AsyncGenerator[datastore.Client, None]:
    config = neo4jdb.Config(
        kind="neo4j",
        uri=db_uri,
        auth=neo4jdb.AuthConfig(username=db_auth[0], password=db_auth[1]),
    )

    client = await datastore.create(config)

    airports_data_set_path = "../data/airport_dataset.csv"
    amenities_data_set_path = "../data/amenity_dataset.csv"
    flights_data_set_path = "../data/flights_dataset.csv"
    policies_data_set_path = "../data/cymbalair_policy.csv"

    airport, amenities, flights, policies = await client.load_dataset(
        airports_data_set_path,
        amenities_data_set_path,
        flights_data_set_path,
        policies_data_set_path,
    )

    await client.initialize_data([], amenities, [], [])

    if client is None:
        raise TypeError("datastore creation failure")
    yield client
    await client.close()


async def test_amenity_init_id(data_set: neo4jdb.Client):
    amenity = await data_set.get_amenity(35)

    expected_amenity = models.Amenity(
        id=35,
        name="Airport Information Desk",
        description="Information desk offering assistance with flight information, directions, and other airport services.",
        location="Arrivals Hall",
        terminal="All Terminals",
        category="facility",
        hour="24/7",
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
        embedding=None,
    )

    assert amenity == expected_amenity
