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

import os

from langchain.agents import AgentType, initialize_agent
from langchain.agents.agent import AgentExecutor
from langchain.globals import set_verbose  # type: ignore
from langchain.llms.vertexai import VertexAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import ChatPromptTemplate

from tools import convert_date, initialize_tools
import aiohttp

set_verbose(bool(os.getenv("DEBUG", default=False)))
connector = None


class ClientAgent:
    client: aiohttp.ClientSession
    agent: AgentExecutor

    def __init__(self, client, agent) -> None:
        self.client = client
        self.agent = agent


async def get_connector():
    if connector is None:
        connector = aiohttp.TCPConnector()
    return connector


# Agent
async def init_agent() -> ClientAgent:
    """Load an agent executor with tools and LLM"""
    print("Initializing agent..")
    llm = VertexAI(max_output_tokens=512)
    memory = ConversationBufferMemory(
        memory_key="chat_history", input_key="input", output_key="output"
    )
    client = aiohttp.ClientSession(connector=await get_connector())
    tools = await initialize_tools(client)
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
    # Create new prompt template
    tool_strings = "\n".join([f"> {tool.name}: {tool.description}" for tool in tools])
    tool_names = ", ".join([tool.name for tool in tools])
    format_instructions = FORMAT_INSTRUCTIONS.format(
        tool_names=tool_names,
    )
    date = convert_date("today")
    today = f"Today is {date}."
    template = "\n\n".join([PREFIX, tool_strings, format_instructions, SUFFIX, today])
    human_message_template = "{input}\n\n{agent_scratchpad}"
    prompt = ChatPromptTemplate.from_messages(
        [("system", template), ("human", human_message_template)]
    )
    agent.agent.llm_chain.prompt = prompt  # type: ignore

    return ClientAgent(client, agent)


PREFIX = """SFO Airport Assistant helps travelers find their way at the airport.

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to
complex multi-query questions that require passing results from one query to another. As a language model, Assistant is
able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding
conversations and provide responses that are coherent and relevant to the topic at hand.

Overall, Assistant is a powerful tool that can help answer a wide range of questions pertaining to the San
Francisco Airport. SFO Airport Assistant is here to assist. It currently does not have access to user info.

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

SUFFIX = """Begin! Use tools if necessary. Respond directly if appropriate.
If using a tool, reminder to ALWAYS respond with a valid json blob of a single action.
Format is Action:```$JSON_BLOB```then Observation:.
Thought:

Previous conversation history:
{chat_history}
"""
