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
from datetime import date
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, TCPConnector
from fastapi import HTTPException
from langchain.agents import AgentType, initialize_agent
from langchain.agents.agent import AgentExecutor
from langchain.globals import set_verbose  # type: ignore
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain.prompts.chat import ChatPromptTemplate
from langchain.tools import StructuredTool
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_google_vertexai import VertexAI

from ..orchestrator import BaseOrchestrator, classproperty
from .tools import initialize_tools

set_verbose(bool(os.getenv("DEBUG", default=False)))
MODEL = "gemini-pro"
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
    def initialize_chat_model(cls, client: ClientSession) -> "UserChatModel":
        model = GenerativeModel(MODEL, tools=[assistant_tool()])
        function_calling_session = model.start_chat()
        return UserChatModel(client, function_calling_session)

    async def close(self):
        await self.client.close()

    async def invoke(self, prompt: str) -> Dict[str, Any]:
        today_date = date.today().strftime("%Y-%m-%d")
        today = f"Today is {today_date}."
        model_response = self.request_chat_model(prompt + today)
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
        try:
            model_response = self.chat.send_message(prompt)
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")
        return model_response

    async def request_function(self, function_call):
        url = function_request(function_call["name"])
        params = function_call["args"]
        print(f"function url is {url}")
        print(f"params is {params}")
        response = await self.client.get(
            url=f"{BASE_URL}/{url}",
            params=params,
            headers=get_headers(self.client),
        )
        response = await response.json()
        return response


class FunctionCallingOrchestrator(BaseOrchestrator):
    _user_sessions: Dict[str, UserChatModel] = {}
    # aiohttp context
    connector = None

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
        chat = UserChatModel.initialize_chat_model(client)
        self._user_sessions[id] = chat

    async def user_session_invoke(self, uuid: str, prompt: str) -> str:
        user_session = self.get_user_session(uuid)
        # Send prompt to LLM
        response = await user_session.invoke(prompt)
        return response["output"]

    async def user_session_reset(self, uuid: str):
        user_session = self.get_user_session(uuid)
        await user_session.close()
        del user_session

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

    def close_clients(self):
        close_client_tasks = [
            asyncio.create_task(a.close()) for a in self._user_sessions.values()
        ]
        asyncio.gather(*close_client_tasks)
