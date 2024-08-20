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

from typing import Any, AsyncGenerator, List

import pytest
import pytest_asyncio

import models

from .. import datastore
from . import neo4j_graph
from .test_data import amenities_query_embedding1, amenities_query_embedding2
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
async def ds(
    db_uri: str,
    db_auth: tuple,
) -> AsyncGenerator[datastore.Client, None]:
    config = neo4j_graph.Config(
        kind="neo4j",
        uri=db_uri,
        auth=neo4j_graph.AuthConfig(username=db_auth[0], password=db_auth[1]),
    )

    ds = await datastore.create(config)

    airports_data_set_path = "../data/airport_dataset.csv"
    amenities_data_set_path = "../data/amenity_dataset.csv"
    flights_data_set_path = "../data/flights_dataset.csv"
    policies_data_set_path = "../data/cymbalair_policy.csv"

    airport, amenities, flights, policies = await ds.load_dataset(
        airports_data_set_path,
        amenities_data_set_path,
        flights_data_set_path,
        policies_data_set_path,
    )

    await ds.initialize_data([], amenities, [], [])

    if ds is None:
        raise TypeError("datastore creation failure")
    yield ds
    await ds.close()


# Test nodes


async def test_total_amenity_nodes_count(ds: neo4j_graph.Client):
    async with ds.driver.session() as session:
        result = await session.run("MATCH (a: Amenity) RETURN count(a) AS count")
        record = await result.single()
        count = record["count"]
        print(count)

    expected_count = 127
    assert (
        count == expected_count
    ), f"Expected {expected_count} nodes, but found {count}"


async def test_get_amenity_id(ds: neo4j_graph.Client):
    amenity = await ds.get_amenity(35)

    assert amenity, f"No amenity found with id 35"

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


async def test_total_category_nodes_count(ds: neo4j_graph.Client):
    async with ds.driver.session() as session:
        result = await session.run("MATCH (c: Category) RETURN count(c) AS count")
        record = await result.single()
        count = record["count"]
        print(count)

    expected_count = 3
    assert (
        count == expected_count
    ), f"Expected {expected_count} nodes, but found {count}"


# Test relationships


async def test_total_belongs_to_relationships_count(ds: neo4j_graph.Client):
    async with ds.driver.session() as session:
        result = await session.run(
            "MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS count"
        )
        record = await result.single()
        count = record["count"]
        print(count)

    expected_count = 127
    assert (
        count == expected_count
    ), f"Expected {expected_count} BELONGS_TO relationships, but found {count}"


async def test_total_similar_to_relationships_count(ds: neo4j_graph.Client):
    async with ds.driver.session() as session:
        result = await session.run(
            # Lower-case relationship naming due to graph generation output format
            "MATCH ()-[r:Similar_to]->() RETURN count(r) AS count"
        )
        record = await result.single()
        count = record["count"]
        print(count)

    # Bi-directional pairs are counted only once
    expected_count = 217
    assert (
        count == expected_count
    ), f"Expected {expected_count} BELONGS_TO relationships, but found {count}"


amenities_search_test_data = [
    pytest.param(
        # "Where can I look for luxury goods?"
        amenities_query_embedding2,
        None,  # similarity threshold value
        2,  # top_k value
        [
            {
                "source_name": "Gucci Duty Free",
                "source_description": "Luxury brand duty-free shop offering designer clothing, accessories, and fragrances.",
                "source_location": "Gate E9",
                "source_terminal": "International Terminal A",
                "source_category": "shop",
                "source_hour": "Daily 7:00 am-10:00 pm",
                "relationship_type": "Similar_to",
                "target_name": "Dufry Duty Free",
                "target_description": "Duty-free shop offering a large selection of luxury goods, including perfumes, cosmetics, and liquor.",
                "target_location": "Gate E2",
                "target_terminal": "International Terminal A",
                "target_category": "shop",
                "target_hour": "Daily 7:00 am-10:00 pm",
            },
            {
                "source_name": "Gucci Duty Free",
                "source_description": "Luxury brand duty-free shop offering designer clothing, accessories, and fragrances.",
                "source_location": "Gate E9",
                "source_terminal": "International Terminal A",
                "source_category": "shop",
                "source_hour": "Daily 7:00 am-10:00 pm",
                "relationship_type": "Similar_to",
                "target_name": "Hermes Duty Free",
                "target_description": "High-end French brand duty-free shop offering luxury goods and accessories.",
                "target_location": "Gate E18",
                "target_terminal": "International Terminal A",
                "target_category": "shop",
                "target_hour": "Daily 7:00 am-10:00 pm",
            },
        ],
        id="search_luxury_goods",
    ),
]


@pytest.mark.parametrize(
    "query_embedding, similarity_threshold, top_k, expected", amenities_search_test_data
)
async def test_amenities_search(
    ds: neo4j_graph.Client,
    query_embedding: List[float],
    similarity_threshold: float,
    top_k: int,
    expected: List[Any],
):
    res = await ds.amenities_search(query_embedding, similarity_threshold, top_k)
    assert res == expected
