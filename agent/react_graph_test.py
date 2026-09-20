# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import MemorySaver
from toolbox_langchain import ToolboxTool

from agent import react_graph


@pytest.fixture
def make_tool():
    def make(name, output="null"):
        tool = MagicMock(spec=ToolboxTool)
        tool.name = name
        tool.ainvoke = AsyncMock(return_value=output)
        # Model Toolbox's authentication metadata without contacting a server.
        tool._ToolboxTool__core_tool = SimpleNamespace(
            _required_authz_tokens=[],
            _required_authn_params=(
                {"user_id": ["my_google_service"]} if name == "list_tickets" else {}
            ),
        )
        tool.add_auth_token_getters.return_value = tool
        return tool

    return make


@pytest.fixture
def run_graph(monkeypatch, make_tool):
    def run(tools, calls, auth_token="test-token"):
        model_inputs = []

        async def respond(prompt):
            model_inputs.append(prompt.to_messages())
            if len(model_inputs) == 1:
                return AIMessage(content="", tool_calls=calls)
            assert len(model_inputs) == 2, "Unexpected extra model invocation"
            return AIMessage(content="Done.")

        model = MagicMock()
        model.bind_tools.return_value = RunnableLambda(respond)
        monkeypatch.setattr(react_graph, "ChatVertexAI", lambda **kwargs: model)

        async def invoke():
            graph = await react_graph.create_graph(
                tools=tools,
                insert_ticket=make_tool("insert_ticket"),
                validate_ticket=make_tool("validate_ticket"),
                checkpointer=MemorySaver(),
                prompt=ChatPromptTemplate.from_messages(
                    [("placeholder", "{messages}")]
                ),
                model_name="unused-test-model",
                debug=False,
            )
            configurable = {"thread_id": "ticket-result-test"}
            if auth_token is not None:
                configurable["auth_token_getters"] = {
                    "my_google_service": lambda: auth_token
                }
            return await graph.ainvoke(
                {"messages": [HumanMessage(content="List my booked flights.")]},
                config={"configurable": configurable, "recursion_limit": 10},
            )

        state = asyncio.run(invoke())
        model.bind_tools.assert_called_once_with(tools)
        return state, model_inputs

    return run


def tool_call(name="list_tickets", call_id="tickets-1", args=None):
    return {"name": name, "id": call_id, "args": args or {}}


@pytest.mark.parametrize("output", [None, [], "null", " NULL ", "[]"])
def test_empty_tickets_reach_model_as_success(make_tool, run_graph, output):
    tool = make_tool("list_tickets", output)
    state, model_inputs = run_graph([tool], [tool_call()])

    expected = "No booked flights were found for this user."
    assert len(model_inputs) == 2
    message = model_inputs[1][-1]
    assert isinstance(message, ToolMessage)
    assert (message.name, message.tool_call_id, message.content) == (
        "list_tickets",
        "tickets-1",
        expected,
    )
    assert state["messages"][-2] == message
    tool.ainvoke.assert_awaited_once_with({})
    getters = tool.add_auth_token_getters.call_args.args[0]
    assert set(getters) == {"my_google_service"}
    assert getters["my_google_service"]() == "test-token"


@pytest.mark.parametrize(
    "name,output",
    [
        ("list_tickets", '[{"flight_number": "123"}]'),
        ("list_tickets", "not valid JSON"),
        ("list_flights", "null"),
    ],
)
def test_other_results_reach_model_unchanged(make_tool, run_graph, name, output):
    tool = make_tool(name, output)
    _, model_inputs = run_graph([tool], [tool_call(name)])

    message = model_inputs[1][-1]
    assert isinstance(message, ToolMessage)
    assert (message.name, message.tool_call_id, message.content) == (
        name,
        "tickets-1",
        output,
    )
    tool.ainvoke.assert_awaited_once_with({})


def test_ticket_query_failure_is_not_empty_success(make_tool, run_graph):
    tool = make_tool("list_tickets")
    tool.ainvoke.side_effect = RuntimeError("database unavailable")
    _, model_inputs = run_graph([tool], [tool_call()])

    message = model_inputs[1][-1]
    assert isinstance(message, ToolMessage)
    assert (message.name, message.tool_call_id, message.content) == (
        "list_tickets",
        "tickets-1",
        "Error executing tool list_tickets: database unavailable",
    )
    tool.ainvoke.assert_awaited_once_with({})


@pytest.mark.parametrize("auth_token", [None, ""])
def test_ticket_query_requires_login(make_tool, run_graph, auth_token):
    tool = make_tool("list_tickets")
    state, model_inputs = run_graph([tool], [tool_call()], auth_token)

    assert len(model_inputs) == 1
    assert state["messages"][-1].content == (
        "This action requires you to be signed in. Please log in and then try again."
    )
    assert not any(isinstance(message, ToolMessage) for message in state["messages"])
    tool.ainvoke.assert_not_awaited()
    tool.add_auth_token_getters.assert_not_called()


def test_multiple_calls_preserve_identity_order_and_arguments(make_tool, run_graph):
    tickets = make_tool("list_tickets")
    flights = make_tool("list_flights", '[{"flight_number": "456"}]')
    calls = [
        tool_call("list_flights", "flights-1", {"departure_airport": "SFO"}),
        tool_call("list_tickets", "tickets-2"),
    ]
    _, model_inputs = run_graph([tickets, flights], calls)

    messages = [m for m in model_inputs[1] if isinstance(m, ToolMessage)]
    assert [(m.name, m.tool_call_id, m.content) for m in messages] == [
        ("list_flights", "flights-1", '[{"flight_number": "456"}]'),
        ("list_tickets", "tickets-2", "No booked flights were found for this user."),
    ]
    flights.ainvoke.assert_awaited_once_with({"departure_airport": "SFO"})
    tickets.ainvoke.assert_awaited_once_with({})
