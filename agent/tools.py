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
from typing import Optional

from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.oauth2.id_token import fetch_id_token
from toolbox_langchain import ToolboxClient

BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
TOOLBOX_URL = os.getenv("TOOLBOX_URL", default="http://127.0.0.1:5000")


def __get_client_headers() -> Optional[dict[str, str]]:
    """
    Fetches a Google Cloud identity token for authenticating with the Toolbox
    service.

    This function uses the application's default credentials to generate an
    identity token.

    Returns:
        Optional[dict[str, str]]: A dictionary containing the Authorization
        header if authentication is successful, otherwise None.
    """
    try:
        id_token = fetch_id_token(Request(), TOOLBOX_URL)
        return {"Authorization": f"Bearer {id_token}"}
    except DefaultCredentialsError:
        # Inform the user that token generation failed, which is expected
        # for local runs, and continue without authentication.
        print(
            "GOOGLE_APPLICATION_CREDENTIALS env var is not set. Proceeding without setting client authentication header."
        )
        return None


# Tools for agent
async def initialize_tools():
    client = ToolboxClient(TOOLBOX_URL, client_headers=__get_client_headers())
    tools = await client.aload_toolset("cymbal_air")

    # Load insert_ticket and validate_ticket tools separately to implement
    # human-in-the-loop.
    insert_ticket = await client.aload_tool("insert_ticket")
    validate_ticket = await client.aload_tool("validate_ticket")

    return (tools, insert_ticket, validate_ticket)


def get_confirmation_needing_tools():
    return ["insert_ticket"]
