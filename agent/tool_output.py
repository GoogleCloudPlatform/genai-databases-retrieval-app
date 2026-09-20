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

from typing import Any

NO_BOOKED_FLIGHTS_MESSAGE = "No booked flights were found for this user."


def normalize_tool_output(tool_name: str, output: Any) -> Any:
    """Make an empty ticket query unambiguous to the agent."""
    if tool_name != "list_tickets":
        return output

    if output is None or (isinstance(output, list) and not output):
        return NO_BOOKED_FLIGHTS_MESSAGE

    if isinstance(output, str) and output.strip().lower() in {"null", "[]"}:
        return NO_BOOKED_FLIGHTS_MESSAGE

    return output
