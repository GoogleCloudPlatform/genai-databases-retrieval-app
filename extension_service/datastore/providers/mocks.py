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

import asyncpg
from collections import OrderedDict
from typing import List
from . import postgres


"""
Mock record class since there is no option to create asyncpg Record objects
from Python code.
"""
class MockRecord(OrderedDict):
    def __getitem__(self, key_or_index):
        if isinstance(key_or_index, int):
            return list(self.values())[key_or_index]

        return super().__getitem__(key_or_index)


class MockAsyncpgPool:
    async def fetch(self, query, *args) -> List[MockRecord]:
        mockRecord = MockRecord([
            ('iata', 'FOO'),
            ('name', 'Foo Bar'),
            ('city', 'baz'),
            ('country', 'bundy'),
        ])
        return [mockRecord] 

async def create_postgres_provider() -> "Client":
    mockPool = MockAsyncpgPool
    mockCl = postgres.Client(mockPool)
    return mockCl
