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

import os

from toolbox_core import auth_methods
from toolbox_langchain import ToolboxClient

TOOLBOX_URL = os.getenv("TOOLBOX_URL", default="http://127.0.0.1:5000")


# Tools for agent
async def initialize_tools():
    auth_token_provider = auth_methods.aget_google_id_token(TOOLBOX_URL)
    client = ToolboxClient(
        TOOLBOX_URL, client_headers={"Authorization": auth_token_provider}
    )
    tools = await client.aload_toolset("cymbal_air")

    # Load insert_ticket and validate_ticket tools separately to implement
    # human-in-the-loop.
    insert_ticket = await client.aload_tool("insert_ticket")
    validate_ticket = await client.aload_tool("validate_ticket")

    return (tools, insert_ticket, validate_ticket)


def get_confirmation_needing_tools():
    return ["insert_ticket"]


def get_auth_tools():
    return [
        "insert_ticket",
        "list_tickets",
    ]
