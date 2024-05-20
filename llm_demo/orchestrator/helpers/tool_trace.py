# Copyright 2024 Google LLC
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

from typing import List


class ToolTrace:
    """
    Tool Trace is used to track the traces associated with a specific user.
    These traces are flushed to the UI as part of response after response is generated.
    """

    curr_log: List[str] = []

    def __init__(self):
        self.curr_log = []

    def add_message(self, message: str):
        """Add message information to trace."""
        self.curr_log.append(message)

    def flush(self):
        """Clear trace for the current user query."""
        curr_log_str = " ".join(self.curr_log)
        self.curr_log = []
        return curr_log_str
