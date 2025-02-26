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
from typing import Callable, Optional

from toolbox_langchain import ToolboxClient

BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
TOOLBOX_URL = os.getenv("TOOLBOX_URL", default="http://127.0.0.1:5000")


# Tools for agent
async def initialize_tools(get_user_id_token: Callable[[], Optional[str]]):
    auth_tokens = {"my_google_service": get_user_id_token}
    client = ToolboxClient(TOOLBOX_URL)
    tools = await client.aload_toolset("cymbal_air", auth_tokens)
    insert_ticket = await client.aload_tool("insert_ticket", auth_tokens)
    validate_ticket = await client.aload_tool("validate_ticket", auth_tokens)

    return (tools, insert_ticket, validate_ticket)


def get_confirmation_needing_tools():
    return ["insert_ticket"]
