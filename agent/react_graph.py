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
import uuid
from typing import Annotated, Literal, Sequence, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolCall,
    ToolMessage,
)
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from toolbox_langchain import ToolboxTool

from .tools import (
    get_auth_tools,
    get_confirmation_needing_tools,
)


class UserState(TypedDict):
    """
    State with messages for each session/user.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]


def __is_logged_in(config: RunnableConfig) -> bool:
    """
    Checks if the user is logged in based on the provided config.
    """
    return bool(
        config
        and "configurable" in config
        and "auth_token_getters" in config["configurable"]
        and "my_google_service" in config["configurable"]["auth_token_getters"]
        and config["configurable"]["auth_token_getters"]["my_google_service"]()
    )


def __get_tool_to_run(tool: ToolboxTool, config: RunnableConfig):
    if (
        config
        and "configurable" in config
        and "auth_token_getters" in config["configurable"]
    ):
        auth_token_getters = config["configurable"]["auth_token_getters"]
        if auth_token_getters:

            # The `add_auth_token_getters` method requires that all provided
            # getters are used by the tool. To prevent validation errors,
            # filter the incoming getters to include only those that this
            # specific tool requires.
            core_tool = tool._ToolboxTool__core_tool  # type:ignore
            required_auth_keys = set(core_tool._required_authz_tokens)
            for auth_list in core_tool._required_authn_params.values():
                required_auth_keys.update(auth_list)
            filtered_getters = {
                k: v for k, v in auth_token_getters.items() if k in required_auth_keys
            }
            if filtered_getters:
                return tool.add_auth_token_getters(filtered_getters)
    return tool


async def create_graph(
    tools: list[ToolboxTool],
    insert_ticket: ToolboxTool,
    validate_ticket: ToolboxTool,
    checkpointer: MemorySaver,
    prompt: ChatPromptTemplate,
    model_name: str,
    debug: bool,
):
    """
    Creates a graph that works with a chat model that utilizes tool calling.

    Args:
        tools: A list of ToolboxTools that will bind with the chat model.
        insert_ticket: A ToolboxTool that inserts ticket for the logged in user.
        validate_ticket: A ToolboxTool that validates the given flight data.
        checkpointer: The checkpoint saver object. This is useful for persisting
            the state of the graph (e.g., as chat memory).
        prompt: Initial prompt for the model. This applies to messages before they
            are passed into the LLM.
        model_name: The chat model name.

    Returns:
        A compilled LangChain runnable that can be used for chat interactions.

    The resulting graph looks like this:
        [*]
         └──> Agent
                 ├──(No tool calls)──> [*]
                 └──(Tool calls)──> Request Login?
                                                ├──(No)──> Tools ──> Agent
                                                ├──(Yes, but not logged in)──> [*]
                                                └──(Yes, and logged in)──> Needs Confirmation?
                                                                                            ├──(No)──> Tools ──> Agent
                                                                                            └──(Yes)──> Booking Validation ──> Insert Ticket ──> [*]
    """

    # tool node
    async def tool_node(state: UserState, config: RunnableConfig):
        last_message = state["messages"][-1]
        tool_messages = []

        if not hasattr(last_message, "tool_calls"):
            return {"messages": []}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            # Find the corresponding tool from the provided list
            selected_tool = next((t for t in tools if t.name == tool_name), None)

            if not selected_tool:
                # Handle case where the model hallucinates a tool name
                output = f"Error: Tool '{tool_name}' not found."
            else:
                try:
                    tool_to_run: ToolboxTool = __get_tool_to_run(selected_tool, config)
                    # Manually invoke the tool with its arguments
                    output = await tool_to_run.ainvoke(tool_call["args"])
                except Exception as e:
                    output = f"Error executing tool {tool_name}: {e}"

            # Create a ToolMessage with the result and original tool_call_id
            tool_messages.append(
                ToolMessage(
                    name=tool_to_run.name,
                    content=output,
                    tool_call_id=tool_call["id"],
                )
            )

        return {"messages": tool_messages}

    # model node
    model = ChatVertexAI(max_output_tokens=512, model_name=model_name, temperature=0.0)

    # Bind the tools with the LLM.
    model_with_tools = model.bind_tools(tools)

    # Add the prompt to the model to create a model runnable
    model_runnable = prompt | model_with_tools

    async def acall_model(state: UserState, config: RunnableConfig):
        """
        The node representing async function that calls the model.
        After invoking model, it will return AIMessage back to the user.
        """
        messages = state["messages"]
        res = await model_runnable.ainvoke({"messages": messages}, config)
        return {"messages": [res]}

    def request_login_node(_: UserState):
        """
        If the user needs to log in, this node sends a message to the user.
        """
        return {
            "messages": [
                AIMessage(
                    content="This action requires you to be signed in. Please log in and then try again."
                )
            ]
        }

    def agent_should_continue(
        state: UserState, config: RunnableConfig
    ) -> Literal["booking_validation", "continue", "request_login", "end"]:
        """
        Function to determine which node is called after the agent node.
        """
        messages = state["messages"]
        last_message = messages[-1]

        # First check if the last message has tool calls.
        if not hasattr(last_message, "tool_calls") or len(last_message.tool_calls) == 0:
            return "end"

        # Next, check if any tool requires authentication.
        for tool_call in last_message.tool_calls:
            if tool_call["name"] in get_auth_tools():
                if not __is_logged_in(config):
                    return "request_login"

        # If authentication passes, then check if any tool needs user confirmation.
        for tool_call in last_message.tool_calls:
            if tool_call["name"] in get_confirmation_needing_tools():
                if tool_call["name"] == "insert_ticket":
                    return "booking_validation"

        # If no special conditions are met, proceed to the "tool" node.
        return "continue"

    async def booking_validation_node(state: UserState):
        """
        The node representing async function that validate the ticket.
        After ticket validation, it will return AIMessage with updated ticket args.
        """
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
            tool_call = last_message.tool_calls[0]
            # Run ticket validation and return the correct ticket information
            flight_info = await validate_ticket.ainvoke(tool_call.get("args"))
            flight_info = json.loads(flight_info)
            flight_info = flight_info[0]

            new_message = AIMessage(
                content="Please confirm if you would like to book the ticket.",
                tool_calls=[
                    ToolCall(
                        id=str(uuid.uuid4()),
                        name=tool_call.get("name"),
                        args=flight_info,
                    )
                ],
                additional_kwargs={"confirmation": True},
            )
            return {"messages": [new_message]}

    def booking_should_continue(state: UserState) -> Literal["continue", "agent"]:
        """
        Function to determine which node is called after human response on ticket booking.
        """
        messages = state["messages"]
        last_message = messages[-1]
        # If last message makes a tool call, then we route to the
        # "insert_ticket" node to proceed with booking.
        if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
            return "continue"
        # Otherwise, send response back to agent
        return "agent"

    async def insert_ticket_node(state: UserState, config: RunnableConfig):
        """
        Node to update human response.
        """
        messages = state["messages"]
        last_message = messages[-1]
        # Run insert ticket
        if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
            tool_call = last_message.tool_calls[0]
            tool_args = tool_call.get("args")
            __insert_ticket = __get_tool_to_run(insert_ticket, config)
            output = await __insert_ticket.ainvoke(tool_args)
            human_message = HumanMessage(content="Looks good to me. Book it!")
            ai_message = AIMessage(
                content=(
                    "Your flight has been successfully booked."
                    if output == "null"
                    else output
                )
            )
            return {"messages": [human_message, ai_message]}

    # Define constant node strings
    AGENT_NODE = "agent"
    TOOL_NODE = "tools"
    BOOKING_VALIDATION_NODE = "booking_validation"
    INSERT_TICKET_NODE = "insert_ticket"
    REQUEST_LOGIN_NODE = "request_login"

    # Define a new graph
    llm_graph = StateGraph(UserState)
    llm_graph.add_node(AGENT_NODE, RunnableLambda(acall_model))
    llm_graph.add_node(TOOL_NODE, tool_node)
    llm_graph.add_node(BOOKING_VALIDATION_NODE, RunnableLambda(booking_validation_node))
    llm_graph.add_node(INSERT_TICKET_NODE, RunnableLambda(insert_ticket_node))
    llm_graph.add_node(REQUEST_LOGIN_NODE, request_login_node)

    # Set agent node as the first node to call
    llm_graph.set_entry_point(AGENT_NODE)

    # Add edges
    llm_graph.add_conditional_edges(
        AGENT_NODE,
        agent_should_continue,
        {
            "continue": TOOL_NODE,
            "booking_validation": BOOKING_VALIDATION_NODE,
            "request_login": REQUEST_LOGIN_NODE,
            "end": END,
        },
    )
    llm_graph.add_edge(TOOL_NODE, AGENT_NODE)
    llm_graph.add_conditional_edges(
        BOOKING_VALIDATION_NODE,
        booking_should_continue,
        {"continue": INSERT_TICKET_NODE, "agent": AGENT_NODE},
    )
    llm_graph.add_edge(INSERT_TICKET_NODE, END)
    llm_graph.add_edge(REQUEST_LOGIN_NODE, END)

    # Compile graph into a LangChain Runnable
    langgraph_app = llm_graph.compile(
        checkpointer=checkpointer, debug=debug, interrupt_after=["booking_validation"]
    )
    return langgraph_app
