# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from agent.tool_output import NO_BOOKED_FLIGHTS_MESSAGE, normalize_tool_output


@pytest.mark.parametrize("output", [None, [], "null", " NULL ", "[]"])
def test_normalize_empty_list_tickets_result(output):
    assert normalize_tool_output("list_tickets", output) == NO_BOOKED_FLIGHTS_MESSAGE


def test_preserve_non_empty_list_tickets_result():
    output = '[{"flight_number": "123"}]'

    assert normalize_tool_output("list_tickets", output) == output


def test_preserve_empty_result_for_other_tools():
    assert normalize_tool_output("list_flights", "null") == "null"
