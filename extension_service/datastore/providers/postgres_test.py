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

from collections import OrderedDict
from typing import Dict, cast

import asyncpg
import pytest

import models

from . import postgres


class MockRecord(OrderedDict):
    """
    MockRecord allows us to initialize asyncpg Record objects directly.
    """

    def __getitem__(self, key_or_index):
        if isinstance(key_or_index, int):
            return list(self.values())[key_or_index]

        return super().__getitem__(key_or_index)


class MockAsyncpgPool(asyncpg.Pool):
    def __init__(self, mocks: Dict[str, MockRecord]):
        self.mocks = mocks

    async def fetch(self, query, *args, timeout=None):
        query = " ".join(q.strip() for q in query.splitlines()).strip()
        return self.mocks.get(query)

    async def fetchrow(self, query, *args, timeout=None):
        query = " ".join(q.strip() for q in query.splitlines()).strip()
        return self.mocks.get(query)


async def mock_postgres_provider(mocks: Dict[str, MockRecord]) -> postgres.Client:
    mockPool = cast(asyncpg.Pool, MockAsyncpgPool(mocks))
    mockCl = postgres.Client(mockPool)
    return mockCl


@pytest.mark.asyncio
async def test_get_airport():
    mockRecord = MockRecord(
        [
            ("id", 1),
            ("iata", "FOO"),
            ("name", "Foo Bar"),
            ("city", "baz"),
            ("country", "bundy"),
        ]
    )
    query = "SELECT id, iata, name, city, country FROM airports WHERE id=$1"
    mocks = {query: mockRecord}
    mockCl = await mock_postgres_provider(mocks)
    res = await mockCl.get_airport(1)
    expected_res = models.Airport(
        id=1,
        iata="FOO",
        name="Foo Bar",
        city="baz",
        country="bundy",
    )
    assert res == expected_res


@pytest.mark.asyncio
async def test_get_amenity():
    mockRecord = MockRecord(
        [
            ("id", 1),
            ("name", "FOO"),
            ("description", "Foo Bar"),
            ("location", "baz"),
            ("terminal", "bundy"),
            ("category", "baz bundy"),
            ("hour", "foo bar buz bundy"),
        ]
    )
    query = """
              SELECT id, name, description, location, terminal, category, hour
              FROM amenities WHERE id=$1
            """
    query = " ".join(q.strip() for q in query.splitlines()).strip()
    mocks = {query: mockRecord}
    mockCl = await mock_postgres_provider(mocks)
    res = await mockCl.get_amenity(1)
    expected_res = models.Amenity(
        id=1,
        name="FOO",
        description="Foo Bar",
        location="baz",
        terminal="bundy",
        category="baz bundy",
        hour="foo bar buz bundy",
    )
    assert res == expected_res


@pytest.mark.asyncio
async def test_amenities_search():
    mockRecord = [
        MockRecord(
            [
                ("id", 1),
                ("name", "FOO"),
                ("description", "Foo Bar"),
                ("location", "baz"),
                ("terminal", "bundy"),
                ("category", "baz bundy"),
                ("hour", "foo bar buz bundy"),
            ]
        )
    ]
    query = """
                  SELECT id, name, description, location, terminal, category, hour
                  FROM (
                      SELECT id, name, description, location, terminal, category, hour, 1 - (embedding <=> $1) AS similarity
                      FROM amenities
                      WHERE 1 - (embedding <=> $1) > $2
                      ORDER BY similarity DESC
                     LIMIT $3
                 ) AS sorted_amenities
            """
    query = " ".join(q.strip() for q in query.splitlines()).strip()
    mocks = {query: mockRecord}
    mockCl = await mock_postgres_provider(mocks)
    res = await mockCl.amenities_search(1, 0.7, 1)
    expected_res = [
        models.Amenity(
            id=1,
            name="FOO",
            description="Foo Bar",
            location="baz",
            terminal="bundy",
            category="baz bundy",
            hour="foo bar buz bundy",
        )
    ]
    assert res == expected_res
