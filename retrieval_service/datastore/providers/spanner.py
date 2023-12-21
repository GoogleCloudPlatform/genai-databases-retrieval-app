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

import asyncio
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any, Dict, Literal, Optional

import asyncpg
from google.cloud import spanner_v1
from pgvector.asyncpg import register_vector
from pydantic import BaseModel
import models

from .. import datastore


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["spanner"]
    database: str


class Client(datastore.Client[Config]):
    __client: spanner_v1.SpannerAsyncClient
    __session: spanner_v1.Session

    @datastore.classproperty
    def kind(cls):
        return "spanner"

    def __init__(
        self, client: spanner_v1.SpannerAsyncClient, session: spanner_v1.Session
    ):
        self.__client = client
        self.__session = session

    @classmethod
    async def create(cls, config: Config) -> "Client":
        client = spanner_v1.SpannerAsyncClient()
        session = await client.create_session(database=Config.database)
        return cls(client, session)
