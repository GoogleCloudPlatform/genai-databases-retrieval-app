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
from .. import datastore


DB_USER = get_env_var("DB_USER", "name of a postgres user")
DB_PASS = get_env_var("DB_PASS", "password for the postgres user")
DB_NAME = get_env_var("DB_NAME", "name of a postgres database")
DB_HOST = get_env_var("DB_HOST", "ip address of a postgres database")


@pytest.fixture(scope="module")
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
    return ds


@pytest.mark.asyncio
async def test_get_airport(ds):
    res = await ds.get_airport_by_id(1)
    expected_res = models.Airport(
        id=1,
        iata="FOO",
        name="Foo Bar",
        city="baz",
        country="bundy",
    )
    assert res == expected_res
