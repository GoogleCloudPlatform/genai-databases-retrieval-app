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

from vertexai.evaluation import MetricPromptTemplateExamples, PointwiseMetric

text_quality_metric = PointwiseMetric(
    metric="text_quality",
    metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template(
        "text_quality"
    ),
)

summarization_quality_metric = PointwiseMetric(
    metric="summarization_quality",
    metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template(
        "summarization_quality"
    ),
)

question_answering_quality_metric = PointwiseMetric(
    metric="question_answering_quality",
    metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template(
        "question_answering_quality"
    ),
)

response_phase_metrics = [
    text_quality_metric,
    summarization_quality_metric,
    question_answering_quality_metric,
]

retrieval_phase_metrics = [
    "tool_call_valid",
    "tool_name_match",
    "tool_parameter_key_match",
    "tool_parameter_kv_match",
]
