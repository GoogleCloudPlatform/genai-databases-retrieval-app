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
from .mocks import create_postgres_provider


@pytest.mark.asyncio
async def test_get_airport():
    mockCl = await create_postgres_provider()
    res = await mockCl.get_airport(1)
    expected_res = [{'iata': 'FOO', 'name': 'Foo Bar', 'city': 'baz', 'country': 'bundy'}]
    assert res == expected_res
