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
import copy
import json
import uuid
from itertools import repeat
from typing import Any, Callable, Dict, Optional, Sequence, Union

from langchain_core.messages import AIMessage, AnyMessage, ToolCall, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.config import get_executor_for_config
from langchain_core.tools import BaseTool
from langchain_core.tools import tool as create_tool
from langgraph.utils import RunnableCallable


def str_output(output: Any) -> str:
    if isinstance(output, str):
        return output
    else:
        try:
            return json.dumps(output)
        except Exception:
            return str(output)


class ToolNode(RunnableCallable):
    """
    A node that runs the tools requested in the last AIMessage. It can be used
    either in StateGraph with a "messages" key or in MessageGraph. If multiple
    tool calls are requested, they will be run in parallel. The output will be
    a list of ToolMessages, one for each tool call.
    """

    def __init__(
        self,
        tools: Sequence[Union[BaseTool, Callable]],
        *,
        name: str = "tools",
        tags: Optional[list[str]] = None,
    ) -> None:
        super().__init__(self._func, self._afunc, name=name, tags=tags, trace=False)
        self.tools_by_name: Dict[str, BaseTool] = {}
        for tool_ in tools:
            if not isinstance(tool_, BaseTool):
                tool_ = create_tool(tool_)
            else:
                base_tool_ = tool_
            if hasattr(tool_, "name"):
                self.tools_by_name[tool_.name] = base_tool_

    def _func(self, input: dict[str, Any], config: RunnableConfig) -> Any:
        if messages := input.get("messages", []):
            output_type = "dict"
            message = messages[-1]
        else:
            raise ValueError("No message found in input")

        if not isinstance(message, AIMessage):
            raise ValueError("Last message is not an AIMessage")

        user_id_token = input.get("user_id_token")

        def run_one(call: ToolCall, user_id_token: Optional[str]):
            args = copy.copy(call["args"]) or {}
            args["user_id_token"] = user_id_token
            output = self.tools_by_name[call["name"]].invoke(args, config)
            tool_call_id = call.get("id") or str(uuid.uuid4())
            return ToolMessage(
                content=str_output(output), name=call["name"], tool_call_id=tool_call_id
            )

        with get_executor_for_config(config) as executor:
            outputs = [
                *executor.map(run_one, message.tool_calls, repeat(user_id_token))
            ]
            if output_type == "list":
                return outputs
            else:
                return {"messages": outputs}

    async def _afunc(self, input: dict[str, Any], config: RunnableConfig) -> Any:
        if messages := input.get("messages", []):
            output_type = "dict"
            message = messages[-1]
        else:
            raise ValueError("No message found in input")

        if not isinstance(message, AIMessage):
            raise ValueError("Last message is not an AIMessage")

        user_id_token = input.get("user_id_token")

        async def run_one(call: ToolCall, user_id_token: Optional[str]):
            args = copy.copy(call["args"]) or {}
            args["user_id_token"] = user_id_token
            output = await self.tools_by_name[call["name"]].ainvoke(args, config)
            tool_call_id = call.get("id") or str(uuid.uuid4())
            return ToolMessage(
                content=str_output(output), name=call["name"], tool_call_id=tool_call_id
            )

        outputs = await asyncio.gather(
            *(run_one(call, user_id_token) for call in message.tool_calls)
        )
        if output_type == "list":
            return outputs
        else:
            return {"messages": outputs}
