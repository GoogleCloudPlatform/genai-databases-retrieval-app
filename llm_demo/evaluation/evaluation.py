# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict, List

from orchestrator import BaseOrchestrator

from .eval_golden import EvalData


async def run_llm_for_eval(
    eval_list: List[EvalData], orc: BaseOrchestrator, session: Dict, session_id: str
) -> List[EvalData]:
    """
    Generate prediction_tool_calls and prediction_output for golden dataset query.
    """
    agent = orc.get_user_session(session_id)
    for eval_data in eval_list:
        query_response = await agent.invoke(eval_data.query)

        # Retrieve prediction_tool_calls from query response
        prediction_tool_calls = []
        for step in query_response.get("intermediate_steps"):
            called_tool = step[0]
            tool_call = {
                "name": called_tool.tool,
                "arguments": called_tool.tool_input,
            }
            prediction_tool_calls.append(tool_call)

        eval_data.prediction_tool_calls = prediction_tool_calls
        eval_data.prediction_output = query_response.get("output")

        if eval_data.reset:
            orc.user_session_reset(session, session_id)
    return eval_list
