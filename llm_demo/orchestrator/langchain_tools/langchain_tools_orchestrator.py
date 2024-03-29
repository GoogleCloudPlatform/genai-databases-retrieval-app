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
from pytz import timezone

from ..orchestrator import BaseOrchestrator, classproperty
from .helpers import ToolTrace
from .tools import get_confirmation_needing_tools, initialize_tools, insert_ticket

set_verbose(bool(os.getenv("DEBUG", default=False)))
BASE_HISTORY = {
    "type": "ai",
    "data": {"content": "Welcome to Cymbal Air!  How may I assist you?"},
}


class UserAgent:
    client: ClientSession
    agent: AgentExecutor

    def __init__(
        self,
        client: ClientSession,
        agent: AgentExecutor,
        memory: ConversationBufferMemory,
    ):
        self.client = client
        self.agent = agent
        self.memory = memory

    @classmethod
    def initialize_agent(
        cls,
        client: ClientSession,
        tools: List[StructuredTool],
        history: List[BaseMessage],
        prompt: ChatPromptTemplate,
        model: str,
    ) -> "UserAgent":
        llm = VertexAI(max_output_tokens=512, model_name=model, temperature=0.0)
        memory = ConversationBufferMemory(
            chat_memory=ChatMessageHistory(messages=history),
            memory_key="chat_history",
            input_key="input",
            output_key="output",
        )
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            memory=memory,
            handle_parsing_errors=True,
            max_iterations=3,
            early_stopping_method="generate",
            return_intermediate_steps=True,
        )
        agent.agent.llm_chain.prompt = prompt  # type: ignore
        return UserAgent(client, agent, memory)

    async def close(self):
        await self.client.close()

    async def invoke(self, prompt: str) -> Dict[str, Any]:
        try:
            response = await self.agent.ainvoke({"input": prompt})
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")
        return response

    def update_tools(self, tools: List[StructuredTool]):
        self.agent.tools = tools

    async def insert_ticket(self, params: str, tool_trace: ToolTrace):
        return await insert_ticket(self.client, params, tool_trace)

    def reset_memory(self, base_message: List[BaseMessage]):
        self.memory.clear()
        self.memory.chat_memory = ChatMessageHistory(messages=base_message)


class LangChainToolsOrchestrator(BaseOrchestrator):
    _user_sessions: Dict[str, UserAgent]
    _user_traces: Dict[str, ToolTrace]
    # aiohttp context
    connector = None

    def __init__(self):
        self._user_sessions = {}
        self._user_traces = {}

    @classproperty
    def kind(cls):
        return "langchain-tools"

    def user_session_exist(self, uuid: str) -> bool:
        return uuid in self._user_sessions

    async def user_session_insert_ticket(self, uuid: str, params: str) -> Any:
        user_session = self.get_user_session(uuid)
        user_traces = self.get_user_traces(uuid)
        response = await user_session.insert_ticket(params, user_traces)
        return response

    def check_and_add_confirmations(cls, response: Dict[str, Any]):
        for step in response.get("intermediate_steps") or []:
            if len(step) > 0:
                # Find the called tool in the step
                called_tool = step[0]
                # Check to see if the agent has made a decision to call Prepare Insert Ticket
                # This tool is a no-op and requires user confirmation before continuing
                if called_tool.tool in cls.confirmation_needing_tools:
                    return {"tool": called_tool.tool, "params": called_tool.tool_input}
        return None

    async def user_session_create(self, session: dict[str, Any]):
        """Create and load an agent executor with tools and LLM."""
        print("Initializing agent..")
        if "uuid" not in session:
            session["uuid"] = str(uuid.uuid4())
        id = session["uuid"]
        if "history" not in session:
            session["history"] = [BASE_HISTORY]
        history = self.parse_messages(session["history"])
        client = await self.create_client_session()
        user_email = ""
        if "user_info" in session:
            user_email = session["user_info"].get("user_email", "")
        tool_trace = ToolTrace()
        tools = await initialize_tools(client, user_email, tool_trace)
        prompt = self.create_prompt_template(tools)
        agent = UserAgent.initialize_agent(client, tools, history, prompt, self.MODEL)
        self._user_sessions[id] = agent
        self._user_traces[id] = tool_trace
        self.confirmation_needing_tools = get_confirmation_needing_tools()
        self.client = client

    async def user_session_invoke(self, uuid: str, prompt: str) -> dict[str, Any]:
        user_session = self.get_user_session(uuid)
        # Send prompt to LLM
        agent_response = await user_session.invoke(prompt)
        # Check for calls that may require confirmation to proceed
        confirmation = self.check_and_add_confirmations(agent_response)
        # Build final response
        response = {}
        response["output"] = agent_response.get("output")
        if confirmation:
            response["confirmation"] = confirmation
        response["trace"] = self.flush_user_trace(uuid)
        return response

    def user_session_reset(self, session: dict[str, Any], uuid: str):
        user_session = self.get_user_session(uuid)
        del session["history"]
        base_history = self.get_base_history(session)
        session["history"] = [base_history]
        history = self.parse_messages(session["history"])
        user_session.reset_memory(history)

    def get_user_session(self, uuid: str) -> UserAgent:
        return self._user_sessions[uuid]

    async def set_user_email(self, uuid: str, user_email: str):
        tools = await initialize_tools(self.client, user_email)
        user_session = self.get_user_session(uuid)
        user_session.update_tools(tools)

    def get_user_traces(self, uuid: str) -> ToolTrace:
        return self._user_traces[uuid]

    def flush_user_trace(self, uuid: str) -> str:
        tool_trace = self.get_user_traces(uuid)
        return tool_trace.flush()

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
                TOOLS_PREFIX,
                tool_strings,
                current_datetime,
                MULTITURN_PROMPT,
                format_instructions,
                SUFFIX,
            ]
        )
        human_message_template = "{input}\n\n{agent_scratchpad}"

        prompt = ChatPromptTemplate.from_messages(
            [("system", template), ("human", human_message_template)]
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
as well as ammenities of San Francisco Airport."""

TOOLS_PREFIX = """
TOOLS:
------

Assistant has access to the following tools:"""

FORMAT_INSTRUCTIONS = """Use a json blob to specify a tool by providing an action key (tool name)
and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Provide only ONE action per $JSON_BLOB, as shown:

```
{{{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}}}
```

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond
Action:
```
{{{{
  "action": "Final Answer",
  "action_input": "Final response to human"
}}}}
```"""

MULTITURN_PROMPT = """Assistant will judge if multiple action need to be taken before returning final response to human.
For example, if user ask 'Where can I get a snack near the gate for flight XX XXXX?'
Actions that will be taken by the assistant is as below:
First, assistant will first complete action for "General Flight and Airport Information".
Next, assistant will complete action for "Search Amenities" based on the gate for that flight.
Lastly, assistant will return final response to human.
"""

SUFFIX = """Begin! Use tools if necessary. Respond directly if appropriate.
If using a tool, reminder to ALWAYS respond with a valid json blob of a single action.
Format is Action:```$JSON_BLOB```then Observation:.
Thought:

Previous conversation history:
{chat_history}
"""
