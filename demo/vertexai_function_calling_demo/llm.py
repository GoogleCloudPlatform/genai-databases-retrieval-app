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
from datetime import date
from typing import Dict, Optional

import aiohttp
import google.oauth2.id_token  # type: ignore
from fastapi import HTTPException
from functions import assistant_tool
from google.auth.transport.requests import Request  # type: ignore
from google.protobuf.json_format import MessageToDict
from vertexai.preview.generative_models import (  # type: ignore
    ChatSession,
    GenerationResponse,
    GenerativeModel,
    Part,
)

MODEL = "gemini-pro"
BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
CREDENTIALS = None

# aiohttp context
connector = None

CLOUD_RUN_AUTHORIZATION_TOKEN = None

func_url = {
    "airports_search": "airports/search",
    "flights_search": "flights/search",
    "list_flights": "flights/search",
    "amenities_search": "amenities/search",
}


class ChatAssistant:
    client: aiohttp.ClientSession
    chat: ChatSession

    def __init__(self, client, chat: ChatSession) -> None:
        self.client = client
        self.chat = chat

    async def invoke(self, prompt: str):
        model_response = self.request_chat_model(prompt)
        print(f"function call response:\n{model_response}")
        part_response = model_response.candidates[0].content.parts[0]
        while "function_call" in part_response._raw_part:
            function_call = MessageToDict(part_response.function_call._pb)
            function_response = await self.request_function(function_call)
            print(f"function response:\n{function_response}")
            part = Part.from_function_response(
                name=function_call["name"],
                response={
                    "content": function_response,
                },
            )
            model_response = self.request_chat_model(part)
            part_response = model_response.candidates[0].content.parts[0]
        if "text" in part_response._raw_part:
            content = part_response.text
            print(f"output content: {content}")
            return {"output": content}
        else:
            raise HTTPException(
                status_code=500, detail="Error: Chat model response unknown"
            )

    def request_chat_model(self, prompt: str):
        model_response = self.chat.send_message(prompt)
        return model_response

    async def request_function(self, function_call):
        function_name = func_url[function_call["name"]]
        params = function_call["args"]
        print(f"function name is {function_name}")
        print(f"params is {params}")
        response = await self.client.get(
            url=f"{BASE_URL}/{function_name}",
            params=params,
            headers=get_headers(self.client),
        )
        response = await response.json()
        return response


chat_assistants: Dict[str, ChatAssistant] = {}


def get_headers(client: aiohttp.ClientSession):
    """Helper method to generate ID tokens for authenticated requests"""
    headers = client.headers
    if not "http://" in BASE_URL:
        # Append ID Token to make authenticated requests to Cloud Run services
        headers["Authorization"] = f"Bearer {get_id_token()}"
    return headers


def get_id_token():
    global CREDENTIALS
    if CREDENTIALS is None:
        CREDENTIALS, _ = google.auth.default()
    if not CREDENTIALS.valid:
        CREDENTIALS.refresh(Request())
    return CREDENTIALS.id_token


async def get_connector():
    global connector
    if connector is None:
        connector = aiohttp.TCPConnector(limit=100)
    return connector


async def handle_error_response(response):
    if response.status != 200:
        return f"Error sending {response.method} request to {str(response.url)}): {await response.text()}"


async def create_client_session(user_id_token: Optional[str]) -> aiohttp.ClientSession:
    headers = {}
    if user_id_token is not None:
        # user-specific query authentication
        headers["User-Id-Token"] = user_id_token

    return aiohttp.ClientSession(
        connector=await get_connector(),
        connector_owner=False,
        headers=headers,
        raise_for_status=True,
    )


async def init_chat_assistant(user_id_token) -> ChatAssistant:
    print("Initializing agent..")
    client = await create_client_session(user_id_token)
    model = GenerativeModel(MODEL, tools=[assistant_tool()])
    func_calling_chat = model.start_chat()
    return ChatAssistant(client, func_calling_chat)
