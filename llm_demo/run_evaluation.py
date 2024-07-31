# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import os
import uuid

import pandas as pd

from evaluation import (
    evaluate_response_phase,
    evaluate_retrieval_phase,
    goldens,
    run_llm_for_eval,
)
from orchestrator import createOrchestrator


def export_metrics_table_csv(retrieval: pd.DataFrame, response: pd.DataFrame):
    """
    Export detailed metrics table to csv file
    """
    retrieval.to_csv("retrieval_eval.csv")
    response.to_csv("response_eval.csv")


async def main():
    ORCHESTRATION_TYPE = os.getenv("ORCHESTRATION_TYPE", default="langchain-tools")
    EXPORT_CSV = bool(os.getenv("EXPORT_CSV", default=False))
    RETRIEVAL_EXPERIMENT_NAME = os.getenv(
        "RETRIEVAL_EXPERIMENT_NAME", default="retrieval-phase-eval"
    )
    RESPONSE_EXPERIMENT_NAME = os.getenv(
        "RESPONSE_EXPERIMENT_NAME", default="response-phase-eval"
    )
    USER_TOKEN_ID = os.getenv("USER_TOKEN_ID", default="")

    # Prepare orchestrator and session
    orc = createOrchestrator(ORCHESTRATION_TYPE)
    session_id = str(uuid.uuid4())
    session = {"uuid": session_id}
    await orc.user_session_create(session)

    # Run evaluation
    eval_lists = await run_llm_for_eval(goldens, orc, session, session_id)
    retrieval_eval_results = evaluate_retrieval_phase(
        eval_lists, RETRIEVAL_EXPERIMENT_NAME
    )
    response_eval_results = evaluate_response_phase(
        eval_lists, RESPONSE_EXPERIMENT_NAME
    )
    print(f"Retrieval phase eval results: {retrieval_eval_results.summary_metrics}")
    print(f"Response phase eval results: {response_eval_results.summary_metrics}")

    if EXPORT_CSV:
        export_metrics_table_csv(
            retrieval_eval_results.metrics_table, response_eval_results.metrics_table
        )


if __name__ == "__main__":
    asyncio.run(main())
