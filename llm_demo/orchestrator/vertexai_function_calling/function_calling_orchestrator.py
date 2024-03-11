# Copyright 2023 Google LLC
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

import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Dict

from aiohttp import ClientSession, TCPConnector
from fastapi import HTTPException
from google.auth.transport.requests import Request  # type: ignore
from google.protobuf.json_format import MessageToDict
from vertexai.preview.generative_models import (  # type: ignore
    ChatSession,
    Content,
    GenerationResponse,
    GenerativeModel,
    Part,
)

from ..orchestrator import BaseOrchestrator, classproperty
from .functions import BASE_URL, assistant_tool, function_request, get_headers

DEBUG = os.getenv("DEBUG", default=False)
BASE_HISTORY = {
    "type": "ai",
    "data": {"content": "Welcome to Cymbal Air!  How may I assist you?"},
}


class UserChatModel:
    client: ClientSession
    chat: ChatSession

    def __init__(self, client: ClientSession, chat: ChatSession):
        self.client = client
        self.chat = chat

    @classmethod
    def initialize_chat_model(
        cls, client: ClientSession, model: str
    ) -> "UserChatModel":
        chat_model = GenerativeModel(model, tools=[assistant_tool()])
        function_calling_session = chat_model.start_chat()
        return UserChatModel(client, function_calling_session)

    async def close(self):
        await self.client.close()

    async def invoke(self, input_prompt: str) -> Dict[str, Any]:
        prompt = self.get_prompt()
        model_response = self.request_chat_model(prompt + input_prompt)
        self.debug_log(f"Prompt:\n{prompt}\n\nQuestion: {input_prompt}.")
        self.debug_log(f"\nFunction call response:\n{model_response}")
        part_response = model_response.candidates[0].content.parts[0]

        # implement multi turn chat with while loop
        while "function_call" in part_response._raw_part:
            function_call = MessageToDict(part_response.function_call._pb)
            function_response = await self.request_function(function_call)
            self.debug_log(f"Function response:\n{function_response}")
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
            self.debug_log(f"Output content: {content}")
            return {"output": content}
        else:
            raise HTTPException(
                status_code=500, detail="Error: Chat model response unknown"
            )

    def get_prompt(self) -> str:
        now = datetime.now().strftime("%A, %m/%d/%Y, %H:%M:%S")
        prompt = f"{PREFIX}. Today's date and current time is {now}."
        return prompt

    def debug_log(self, output: str) -> None:
        if DEBUG:
            print(output)

    def request_chat_model(self, prompt: str):
        try:
            model_response = self.chat.send_message(prompt)
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")
        return model_response

    async def request_function(self, function_call):
        url = function_request(function_call["name"])
        params = function_call["args"]
        self.debug_log(f"Function url is {url}.\nParams is {params}.")
        response = await self.client.get(
            url=f"{BASE_URL}/{url}",
            params=params,
            headers=get_headers(self.client),
        )
        response = await response.json()
        return response

    def reset_memory(self, model: str):
        """reinitiate chat model to reset memory."""
        del self.chat
        chat_model = GenerativeModel(model, tools=[assistant_tool()])
        self.chat = chat_model.start_chat()


class FunctionCallingOrchestrator(BaseOrchestrator):
    _user_sessions: Dict[str, UserChatModel]
    # aiohttp context
    connector = None

    def __init__(self):
        self._user_sessions = {}

    @classproperty
    def kind(cls):
        return "vertexai-function-calling"

    def user_session_exist(self, uuid: str) -> bool:
        return uuid in self._user_sessions

    async def user_session_create(self, session: dict[str, Any]):
        """Create and load an agent executor with tools and LLM."""
        print("Initializing agent..")
        if "uuid" not in session:
            session["uuid"] = str(uuid.uuid4())
        id = session["uuid"]
        if "history" not in session:
            session["history"] = [BASE_HISTORY]
        client = await self.create_client_session()
        chat = UserChatModel.initialize_chat_model(client, self.MODEL)
        self._user_sessions[id] = chat

    async def user_session_invoke(self, uuid: str, prompt: str) -> str:
        user_session = self.get_user_session(uuid)
        # Send prompt to LLM
        response = await user_session.invoke(prompt)
        return response["output"]

    def user_session_reset(self, session: dict[str, Any], uuid: str):
        user_session = self.get_user_session(uuid)
        del session["history"]
        base_history = self.get_base_history(session)
        session["history"] = [base_history]
        user_session.reset_memory(self.MODEL)

    def get_user_session(self, uuid: str) -> UserChatModel:
        return self._user_sessions[uuid]

    async def get_connector(self) -> TCPConnector:
        if self.connector is None:
            self.connector = TCPConnector(limit=100)
        return self.connector

    async def create_client_session(self) -> ClientSession:
        return ClientSession(
            connector=await self.get_connector(),
            connector_owner=False,
            headers={},
            raise_for_status=True,
        )

    def get_base_history(self, session: dict[str, Any]):
        if "user_info" in session:
            base_history = {
                "type": "ai",
                "data": {
                    "content": f"Welcome to Cymbal Air, {session['user_info']['name']}!  How may I assist you?"
                },
            }
            return base_history
        return BASE_HISTORY

    def close_clients(self):
        close_client_tasks = [
            asyncio.create_task(a.close()) for a in self._user_sessions.values()
        ]
        asyncio.gather(*close_client_tasks)


PREFIX = """The Cymbal Air Customer Service Assistant helps customers of Cymbal Air with their travel needs.

Cymbal Air (airline unique two letter identifier as CY) is a passenger airline offering convenient flights to many cities around the world from its 
hub in San Francisco. Cymbal Air takes pride in using the latest technology to offer the best customer
service!

Cymbal Air Customer Service Assistant (or just "Assistant" for short) is designed to assist 
with a wide range of tasks, from answering simple questions to complex multi-query questions that 
require passing results from one query to another. Using the latest AI models, Assistant is able to 
generate human-like text based on the input it receives, allowing it to engage in natural-sounding
conversations and provide responses that are coherent and relevant to the topic at hand.

Assistant is a powerful tool that can help answer a wide range of questions pertaining to travel on Cymbal Air
as well as ammenities of San Francisco Airport. 
"""
