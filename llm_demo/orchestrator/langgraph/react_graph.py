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

import json
from typing import Annotated, Literal, Sequence, TypedDict

from aiohttp import ClientSession
from langchain_core.messages import AIMessage, BaseMessage, ToolCall
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_google_vertexai import VertexAI
from langgraph.checkpoint import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep

from .tool_node import ToolNode


class UserState(TypedDict):
    """
    State with messages and ClientSession for each session/user.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id_token: str
    is_last_step: IsLastStep


async def create_graph(
    tools,
    checkpointer: MemorySaver,
    prompt: ChatPromptTemplate,
    model_name: str,
    debug: bool,
):
    """
    Creates a graph that works with a chat model that utilizes tool calling.

    Args:
        tools: A list of StructuredTools that will bind with the chat model.
        checkpointer: The checkpoint saver object. This is useful for persisting
            the state of the graph (e.g., as chat memory).
        prompt: Initial prompt for the model. This applies to messages before they
            are passed into the LLM.
        model_name: The chat model name.

    Returns:
        A compilled LangChain runnable that can be used for chat interactions.

    The resulting graph looks like this:
        [*] --> Start
        Start --> Agent
        Agent --> Tools : continue
        Tools --> Agent
        Agent --> End : end
        End --> [*]
    """
    # tool node
    tool_node = ToolNode(tools)

    # model node
    model = VertexAI(max_output_tokens=512, model_name=model_name, temperature=0.0)

    # Add the prompt to the model to create a model runnable
    model_runnable = prompt | model

    async def acall_model(state: UserState, config: RunnableConfig):
        """
        The node representing async function that calls the model.
        After invoking model, it will return AIMessage back to the user.
        """
        messages = state["messages"]
        res = await model_runnable.ainvoke({"messages": messages}, config)
        response = res.replace("```json", "").replace("```", "")
        try:
            json_response = json.loads(response)
            action = json_response.get("action")
            action_input = json_response.get("action_input")
            if action == "Final Answer":
                new_message = AIMessage(content=action_input)
            else:
                new_message = AIMessage(
                    content="suggesting a tool call",
                    tool_calls=[ToolCall(id="1", name=action, args=action_input)],
                )
        except Exception as e:
            json_response = response
            new_message = AIMessage(
                content="Sorry, failed to generate the right format for response"
            )
        # if model exceed the number of steps and has not yet return a final answer
        if state["is_last_step"] and hasattr(new_message, "tool_calls"):
            return {
                "messages": [
                    AIMessage(
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }
        return {"messages": [new_message]}

    def agent_should_continue(state: UserState) -> Literal["continue", "end"]:
        """
        Function to determine which node is called after the agent node.
        """
        messages = state["messages"]
        last_message = messages[-1]
        # If the LLM makes a tool call, then we route to the "tools" node
        if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
            return "continue"
        # Otherwise, we stop (reply to the user)
        return "end"

    # Define constant node strings
    AGENT_NODE = "agent"
    TOOL_NODE = "tools"

    # Define a new graph
    llm_graph = StateGraph(UserState)
    llm_graph.add_node(AGENT_NODE, RunnableLambda(acall_model))
    llm_graph.add_node(TOOL_NODE, tool_node)

    # Set agent node as the first node to call
    llm_graph.set_entry_point(AGENT_NODE)

    # Add edges
    llm_graph.add_conditional_edges(
        AGENT_NODE, agent_should_continue, {"continue": TOOL_NODE, "end": END}
    )
    llm_graph.add_edge(TOOL_NODE, AGENT_NODE)

    # Compile graph into a LangChain Runnable
    langgraph_app = llm_graph.compile(checkpointer=checkpointer, debug=debug)
    return langgraph_app
