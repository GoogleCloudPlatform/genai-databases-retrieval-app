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

import asyncio
import os
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, Sequence, TypedDict

from aiohttp import ClientSession, TCPConnector
from fastapi import HTTPException
from langchain.globals import set_verbose  # type: ignore
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import StructuredTool
from langgraph.checkpoint import MemorySaver
from langgraph.checkpoint.base import empty_checkpoint
from pytz import timezone

from ..orchestrator import BaseOrchestrator, classproperty
from .react_graph import create_graph
from .tools import initialize_tools

DEBUG = bool(os.getenv("DEBUG", default=False))
set_verbose(DEBUG)
BASE_HISTORY = {
    "type": "ai",
    "data": {"content": "Welcome to Cymbal Air!  How may I assist you?"},
}


class LangGraphOrchestrator(BaseOrchestrator):
    _user_sessions: Dict[str, str]
    # aiohttp context
    connector = None
    client: Optional[ClientSession] = None

    def __init__(self):
        self._user_sessions = {}
        self._langgraph_app = None
        self._checkpointer = None

    @classproperty
    def kind(cls):
        return "langgraph"

    def user_session_exist(self, uuid: str) -> bool:
        return uuid in self._user_sessions

    async def user_session_insert_ticket(self, uuid: str, params: str) -> Any:
        response = await self.user_session_invoke(uuid, None)
        return "ticket booking success"

    async def user_session_decline_ticket(self, uuid: str) -> dict[str, Any]:
        config = self.get_config(uuid)
        human_message = HumanMessage(
            content="I changed my mind. Decline ticket booking."
        )
        self._langgraph_app.update_state(config, {"messages": [human_message]})
        response = await self.user_session_invoke(uuid, None)
        return response

    async def user_session_create(self, session: dict[str, Any]):
        """Create and load an agent executor with tools and LLM."""
        client = await self.create_client_session()
        if self._langgraph_app is None:
            print("Initializing graph..")
            tools = await initialize_tools(client)
            prompt = self.create_prompt_template(tools)
            checkpointer = MemorySaver()
            langgraph_app = await create_graph(
                tools, checkpointer, prompt, self.MODEL, client, DEBUG
            )
            self._checkpointer = checkpointer
            self._langgraph_app = langgraph_app

        print("Initializing session")
        if "uuid" not in session:
            session["uuid"] = str(uuid.uuid4())
        session_id = session["uuid"]
        if "history" not in session:
            session["history"] = [BASE_HISTORY]
        history = self.parse_messages(session["history"])

        config = self.get_config(session_id)
        self._langgraph_app.update_state(config, {"messages": history})
        self._user_sessions[session_id] = ""
        self.client = client

    async def user_session_invoke(
        self, uuid: str, user_prompt: Optional[str]
    ) -> dict[str, Any]:
        config = self.get_config(uuid)
        cur_message_index = (
            len(self._langgraph_app.get_state(config).values["messages"]) - 1
        )
        if user_prompt:
            user_query = [HumanMessage(content=user_prompt)]
            app_input = {
                "messages": user_query,
                "user_id_token": self.get_user_id_token(uuid),
            }
        else:
            app_input = None
        final_state = await self._langgraph_app.ainvoke(
            app_input,
            config=config,
        )
        messages = final_state["messages"]
        # Retrieve tracing information
        trace = self.retrieve_trace(messages[cur_message_index:])
        # Retrieve the last message from the state messages
        last_message = messages[-1]
        output = last_message.content
        # Build final response
        response = {}
        response["output"] = output
        response["trace"] = trace
        # If needs ticket verification
        has_add_kwargs = hasattr(last_message, "additional_kwargs")
        if has_add_kwargs and last_message.additional_kwargs.get("confirmation"):
            tool_call = last_message.tool_calls[0]
            response["confirmation"] = {
                "tool": tool_call.get("name"),
                "params": tool_call.get("args"),
            }
            return response
        response["state"] = final_state
        return response

    def retrieve_trace(self, messages: Sequence[BaseMessage]):
        trace = []
        for m in messages:
            if isinstance(m, ToolMessage):
                trace_info = {"tool_call_id": m.name, "results": m.content}
                add_kwargs = m.additional_kwargs
                if add_kwargs and add_kwargs.get("sql"):
                    trace_info["sql"] = add_kwargs.get("sql")
                trace.append(trace_info)
        return trace

    def user_session_reset(self, session: dict[str, Any], uuid: str):
        del session["history"]
        base_history = self.get_base_history(session)
        session["history"] = [base_history]
        history = self.parse_messages(session["history"])

        # Reset graph checkpointer
        checkpoint = empty_checkpoint()
        config = self.get_config(uuid)
        self._checkpointer.put(config=config, checkpoint=checkpoint, metadata={})

        # Update state with message history
        self._langgraph_app.update_state(config, {"messages": history})

    def get_user_session(self, uuid: str):
        raise NotImplementedError("Irrelevant to LangGraph.")

    def set_user_session_header(self, uuid: str, user_id_token: str):
        self._user_sessions[uuid] = user_id_token

    def get_user_id_token(self, uuid: str) -> Optional[str]:
        return self._user_sessions.get(uuid)

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

    def create_prompt_template(self, tools: List[StructuredTool]) -> ChatPromptTemplate:
        # Create new prompt template
        tool_strings = "\n".join(
            [f"> {tool.name}: {tool.description}" for tool in tools]
        )
        tool_names = ", ".join([tool.name for tool in tools])
        format_instructions = FORMAT_INSTRUCTIONS.format(
            tool_names=tool_names,
        )
        current_datetime = "Today's date and current time is {cur_datetime}."
        template = "\n\n".join(
            [
                PREFIX,
                current_datetime,
                TOOLS_PREFIX,
                tool_strings,
                format_instructions,
                SUFFIX,
            ]
        )

        prompt = ChatPromptTemplate.from_messages(
            [("system", template), ("placeholder", "{messages}")]
        )
        prompt = prompt.partial(cur_datetime=self.get_datetime)
        return prompt

    def get_datetime(self):
        formatter = "%A, %m/%d/%Y, %H:%M:%S"
        now = datetime.now(timezone("US/Pacific"))
        return now.strftime(formatter)

    def parse_messages(self, datas: List[Any]) -> List[BaseMessage]:
        messages: List[BaseMessage] = []
        for data in datas:
            if data["type"] == "human":
                messages.append(HumanMessage(content=data["data"]["content"]))
            elif data["type"] == "ai":
                messages.append(AIMessage(content=data["data"]["content"]))
            else:
                raise Exception("Message type not found.")
        return messages

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

    def get_config(self, uuid: str):
        return {"configurable": {"thread_id": uuid}}

    async def user_session_signout(self, uuid: str):
        checkpoint = empty_checkpoint()
        config = self.get_config(uuid)
        self._checkpointer.put(config=config, checkpoint=checkpoint, metadata={})
        del self._user_sessions[uuid]

    def close_clients(self):
        if self.client:
            close_client_task = asyncio.create_task(self.client.close())
            asyncio.gather(*close_client_task)


PREFIX = """The Cymbal Air Customer Service Assistant helps customers of Cymbal Air with their travel needs.

Cymbal Air (airline unique two letter identifier as CY) is a passenger airline offering convenient flights to many cities around the world from its
hub in San Francisco. Cymbal Air takes pride in using the latest technology to offer the best customer
service!

Cymbal Air Customer Service Assistant (or just "Assistant" for short) is designed to assist
with a wide range of tasks, from answering simple questions to complex multi-query questions that
require passing results from one query to another. Using the latest AI models, Assistant is able to
generate human-like text based on the input it receives, allowing it to engage in natural-sounding
conversations and provide responses that are coherent and relevant to the topic at hand. The assistant should 
not answer questions about other peoples information for privacy reasons. 

Assistant is a powerful tool that can help answer a wide range of questions pertaining to travel on Cymbal Air
as well as ammenities of San Francisco Airport."""

TOOLS_PREFIX = """
TOOLS:
------
Assistant can ask the user to use tools to look up information that may be helpful in answering the users original question. The tools the human can use are:

"""

FORMAT_INSTRUCTIONS = """
When responding, please output a response in one of two formats:

** Option 1:**
Use this is you want to use a tool.
Markdown code snippet formatted in the following schema:
```json
{{{{
  "action": string, \ The action to take. Must be one of {tool_names}
  "action_input": string \ The input to the action
}}}}
```

**Option 2:**
Use this if you want to respond directly to the human.
Markdown code snippet formatted following schema:
```json
{{{{
  "action": "Final Answer",
  "action_input": string \ You should put what you want to return to user here
}}}}
```
"""

SUFFIX = """Begin! Use tools if necessary. Respond directly if appropriate.

Remember to respond with a markdown code snippet of a json a single action, and NOTHING else.
"""
