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

import asyncio
import json
from typing import Dict, List

import pandas as pd
from pydantic import BaseModel, Field
from vertexai.preview.evaluation import EvalTask  # type: ignore
from vertexai.preview.evaluation import _base as evaluation_base

from orchestrator import BaseOrchestrator

from .eval_golden import EvalData, ToolCall


async def run_llm_for_eval(
    eval_list: List[EvalData], orc: BaseOrchestrator, session: Dict, session_id: str
) -> List[EvalData]:
    """
    Generate prediction_tool_calls and prediction_output for golden dataset query.
    """
    agent = orc.get_user_session(session_id)
    for eval_data in eval_list:
        try:
            query_response = await agent.invoke(eval_data.query)
        except Exception as e:
            print(f"error invoking agent: {e}")
        else:
            eval_data.prediction_output = query_response.get("output")

            # Retrieve prediction_tool_calls from query response
            prediction_tool_calls = []
            contexts = []
            for step in query_response.get("intermediate_steps"):
                called_tool = step[0]
                tool_call = ToolCall(
                    name=called_tool.tool,
                    arguments=called_tool.tool_input,
                )
                prediction_tool_calls.append(tool_call)
                context = step[-1]
                contexts.append(context)

            eval_data.prediction_tool_calls = prediction_tool_calls
            eval_data.context = contexts

        if eval_data.reset:
            orc.user_session_reset(session, session_id)
    return eval_list


def evaluate_retrieval_phase(eval_datas: List[EvalData]) -> evaluation_base.EvalResult:
    """
    Run evaluation for the ability of a model to select the right tool and arguments (retrieval phase).
    """
    RETRIEVAL_EXPERIMENT_NAME = "retrieval-phase-eval"
    metrics = ["tool_call_quality"]
    # Prepare evaluation task input
    responses = []
    references = []
    for e in eval_datas:
        responses.append(
            json.dumps(
                {
                    "content": e.content,
                    "tool_calls": [t.model_dump() for t in e.tool_calls],
                }
            )
        )
        references.append(
            json.dumps(
                {
                    "content": e.content,
                    "tool_calls": [t.model_dump() for t in e.prediction_tool_calls],
                }
            )
        )
    eval_dataset = pd.DataFrame(
        {
            "response": responses,
            "reference": references,
        }
    )
    # Run evaluation
    eval_result = EvalTask(
        dataset=eval_dataset,
        metrics=metrics,
        experiment=RETRIEVAL_EXPERIMENT_NAME,
    ).evaluate()
    return eval_result

def evaluate_response_phase(eval_datas: List[EvalData]) -> evaluation_base.EvalResult:
    RESPONSE_EXPERIMENT_NAME = "response-phase-eval"
    metrics = [
        "text_generation_quality",
        "text_generation_factuality",
        "summarization_pointwise_reference_free",
        "qa_pointwise_reference_free",
    ]
    instructions = [
        e.instruction or "answer user query based on context given"
        for e in eval_datas
    ]
    contexts = [e.context or "no data retrieved" for e in eval_datas]
    responses = [e.prediction_output for e in eval_datas]
    eval_dataset = pd.DataFrame(
        {
            "instruction": instructions,
            "context": contexts,
            "response": responses,
        }
    )
    eval_result = evaluate_task(eval_dataset, metrics, RESPONSE_EXPERIMENT_NAME)
    return eval_result
