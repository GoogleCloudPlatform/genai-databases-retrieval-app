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

from toolbox_langchain import ToolboxClient
from google.auth.transport.requests import Request
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2.id_token import fetch_id_token
from warnings import warn


BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
TOOLBOX_URL = os.getenv("TOOLBOX_URL", default="http://127.0.0.1:5000")


def get_token_with_library() -> str:
    """
    Fetches a Google-signed identity token using the google.auth library.

    Returns:
        The identity token as a string.
    """
    try:
        return fetch_id_token(Request(), TOOLBOX_URL)
    except DefaultCredentialsError as e:
        warn(
            "Failed to fetch identity token using google.auth library. "
            "Ensure that the GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly.",
            UserWarning,
        )
        return None

# Tools for agent
async def initialize_tools():
    creds =  get_token_with_library()
    if creds:
        client_headers = {"Authorization": f"Bearer {creds}"}
    else:
        client_headers = None
    client = ToolboxClient(TOOLBOX_URL, client_headers=client_headers)
    tools = await client.aload_toolset("cymbal_air")

    # Load insert_ticket and validate_ticket tools separately to implement
    # human-in-the-loop.
    insert_ticket = await client.aload_tool("insert_ticket")
    validate_ticket = await client.aload_tool("validate_ticket")

    return (tools, insert_ticket, validate_ticket)


def get_confirmation_needing_tools():
    return ["insert_ticket"]
