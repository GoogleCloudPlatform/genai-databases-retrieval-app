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

    async def fetch(self, query, *args):
        return self.mocks.get(query.strip())


async def mock_postgres_provider(mocks: Dict[str, MockRecord]) -> postgres.Client:
    mockPool = cast(asyncpg.Pool, MockAsyncpgPool(mocks))
    mockCl = postgres.Client(mockPool)
    return mockCl


@pytest.mark.asyncio
async def test_get_airport():
    mockRecord = [
        MockRecord(
            [
                ("id", 1),
                ("iata", "FOO"),
                ("name", "Foo Bar"),
                ("city", "baz"),
                ("country", "bundy"),
            ]
        )
    ]
    mocks = {
        "SELECT id, iata, name, city, country FROM airports WHERE id=$1": mockRecord
    }
    mockCl = await mock_postgres_provider(mocks)
    res = await mockCl.get_airport(1)
    expected_res = [
        models.Airport(
            id=1,
            iata="FOO",
            name="Foo Bar",
            city="baz",
            country="bundy",
        )
    ]
    assert res == expected_res


@pytest.mark.asyncio
async def test_airport_search():
    mockRecord = [
        MockRecord(
            [
                ("iata", "FOO"),
                ("name", "Foo Bar"),
                ("city", "baz"),
                ("country", "bundy"),
            ]
        )
    ]
    mockCl = await create_postgres_provider(mockRecord)
    res = await mockCl.airports_search(1, 0.7, 1)
    expected_res = [
        {"iata": "FOO", "name": "Foo Bar", "city": "baz", "country": "bundy"}
    ]
    assert res == expected_res
