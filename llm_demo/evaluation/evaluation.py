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

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from orchestrator import BaseOrchestrator

from .eval_golden import goldens


class EvalData(BaseModel):
    category: Optional[str] = Field(default=None, description="evaluation category")
    query: Optional[str] = Field(default=None, description="user query")
    instruction: Optional[str] = Field(
        default=None, description="instruction to llm system"
    )
    content: Optional[str] = Field(default=None)
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None)
    context: Optional[str] = Field(
        default=None, description="context given to llm in order to answer user query"
    )
    output: Optional[str] = Field(default=None)
    prediction_tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None)
    prediction_output: Optional[str] = Field(default=None)
    reset: bool = Field(
        default=True, description="determine to reset the chat after invoke"
    )


class Evaluation:
    def load_golden_data(self) -> List[EvalData]:
        """
        Load golden dataset into EvalData model.
        """
        eval_datas = []
        for golden in goldens:
            for key in golden:
                cases = golden[key]
                for case in cases:
                    data = EvalData(**case)
                    data.category = key
                    eval_datas.append(data)
        return eval_datas

    async def run_llm_for_eval(
        self, eval_datas: List[EvalData], orc: BaseOrchestrator, session: Dict, uid: str
    ) -> List[EvalData]:
        """
        Generate prediction_tool_calls and prediction_output for golden dataset query.
        """
        agent = orc.get_user_session(uid)
        for eval_data in eval_datas:
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
                orc.user_session_reset(session, uid)
        return eval_datas
