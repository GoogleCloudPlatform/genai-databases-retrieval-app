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
from vertexai.evaluation import EvalTask
from vertexai.evaluation import _base as evaluation_base

from orchestrator import BaseOrchestrator

from .eval_golden import EvalData, ToolCall
from .metrics import response_phase_metrics, retrieval_phase_metrics


async def run_llm_for_eval(
    eval_list: List[EvalData], orc: BaseOrchestrator, session: Dict, session_id: str
) -> List[EvalData]:
    """
    Generate llm_tool_calls and llm_output for golden dataset query.
    This function is only compatible with the langchain-tools orchestration.
    """
    agent = orc.get_user_session(session_id)
    for eval_data in eval_list:
        try:
            query_response = await agent.invoke(eval_data.query)
        except Exception as e:
            print(f"error invoking agent: {e}")
        else:
            eval_data.llm_output = query_response.get("output")

            # Retrieve llm_tool_calls from query response
            llm_tool_calls = []
            contexts = []
            for step in query_response.get("intermediate_steps"):
                called_tool = step[0]
                tool_call = ToolCall(
                    name=called_tool.tool,
                    arguments=called_tool.tool_input,
                )
                llm_tool_calls.append(tool_call)
                context = step[-1]
                contexts.append(context)

            eval_data.llm_tool_calls = llm_tool_calls
            eval_data.context = contexts
            eval_data.prompt = PROMPT
            eval_data.instruction = f"Answer user query based on context given. User query is {eval_data.query}."

        if eval_data.reset:
            orc.user_session_reset(session, session_id)
    return eval_list


def evaluate_retrieval_phase(
    eval_datas: List[EvalData], experiment_name: str
) -> evaluation_base.EvalResult:
    """
    Run evaluation for the ability of a model to select the right tool and arguments (retrieval phase).
    """
    # Prepare evaluation task input
    responses = []
    references = []
    for e in eval_datas:
        references.append(
            json.dumps(
                {
                    "content": e.content,
                    "tool_calls": [t.model_dump() for t in e.tool_calls],
                }
            )
        )
        responses.append(
            json.dumps(
                {
                    "content": e.content,
                    "tool_calls": [t.model_dump() for t in e.llm_tool_calls],
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
        metrics=retrieval_phase_metrics,
        experiment=experiment_name,
    ).evaluate()
    return eval_result


def evaluate_response_phase(
    eval_datas: List[EvalData], experiment_name: str
) -> evaluation_base.EvalResult:
    """
    Run evaluation for the ability of a model to generate a response based on the context given (response phase).
    """
    # Prepare evaluation task input
    instructions = []
    contexts = []
    responses = []
    prompts = []

    for e in eval_datas:
        instructions.append(e.instruction)
        context_str = (
            [json.dumps(c) for c in e.context] if e.context else ["no data retrieved"]
        )
        prompts.append(e.prompt)
        contexts.append(", ".join(context_str))
        responses.append(e.llm_output or "")
    eval_dataset = pd.DataFrame(
        {
            "instruction": instructions,
            "prompt": prompts,
            "context": contexts,
            "response": responses,
        }
    )
    # Run evaluation
    eval_result = EvalTask(
        dataset=eval_dataset,
        metrics=response_phase_metrics,
        experiment=experiment_name,
    ).evaluate()
    return eval_result


PROMPT = """The Cymbal Air Customer Service Assistant helps customers of Cymbal Air with their travel needs.

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
as well as ammenities of San Francisco Airport.

Answer user query based on context or information given.
"""
