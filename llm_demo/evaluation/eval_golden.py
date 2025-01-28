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

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pytz import timezone


class ToolCall(BaseModel):
    """
    Represents tool call by orchestration.
    """

    name: str
    arguments: Dict[str, Any] = Field(
        default={}, description="Query arguments for tool call"
    )


class EvalData(BaseModel):
    """
    Evaluation data model.
    This model represents the information needed for running rapid evaluation with Vertex AI.
    """

    category: Optional[str] = Field(default=None, description="Evaluation category")
    query: Optional[str] = Field(default=None, description="User query")
    instruction: Optional[str] = Field(
        default="",
        description="Part of the input user prompt. It refers to the inference instruction that is sent to you llm",
    )
    content: Optional[str] = Field(
        default=None,
        description="Used in tool call evaluation. Content value is the text output from the model.",
    )
    tool_calls: List[ToolCall] = Field(
        default=[], description="Golden tool call for evaluation"
    )
    prompt: Optional[str] = Field(
        default="",
        description="User input for the Gen AI model or application. It's optional in some cases.",
    )
    context: Optional[List[Dict[str, Any] | List[Dict[str, Any]]]] = Field(
        default=None, description="Context given to llm in order to answer user query"
    )
    output: Optional[str] = Field(
        default=None, description="Golden output for evaluation"
    )
    llm_tool_calls: List[ToolCall] = Field(
        default=[], description="Tool call output from LLM"
    )
    llm_output: str = Field(default="", description="Final output from LLM")
    reset: bool = Field(
        default=True, description="Determine to reset the chat after invoke"
    )


def get_date(day_delta: int):
    DATE_FORMATTER = "%Y-%m-%d"
    retrieved_date = datetime.now(timezone("US/Pacific")) + timedelta(days=day_delta)
    return retrieved_date.strftime(DATE_FORMATTER)


goldens = [
    EvalData(
        category="Search Airport Tool",
        query="What is the airport located in San Francisco?",
        tool_calls=[
            ToolCall(
                name="Search Airport",
                arguments={"country": "United States", "city": "San Francisco"},
            ),
        ],
    ),
    EvalData(
        category="Search Airport Tool",
        query="Tell me more about Denver International Airport?",
        tool_calls=[
            ToolCall(
                name="Search Airport",
                arguments={
                    "country": "United States",
                    "city": "Denver",
                    "name": "Denver International Airport",
                },
            ),
        ],
    ),
    EvalData(
        category="Search Flights By Flight Number Tool",
        query="What is the departure gate for flight CY 922?",
        tool_calls=[
            ToolCall(
                name="Search Flights By Flight Number",
                arguments={
                    "airline": "CY",
                    "flight_number": "922",
                },
            ),
        ],
    ),
    EvalData(
        category="Search Flights By Flight Number Tool",
        query="What is flight CY 888 flying to?",
        tool_calls=[
            ToolCall(
                name="Search Flights By Flight Number",
                arguments={
                    "airline": "CY",
                    "flight_number": "888",
                },
            ),
        ],
    ),
    EvalData(
        category="List Flights Tool",
        query="What flights are headed to JFK tomorrow?",
        tool_calls=[
            ToolCall(
                name="List Flights",
                arguments={
                    "arrival_airport": "JFK",
                    "date": f"{get_date(1)}",
                },
            ),
        ],
    ),
    EvalData(
        category="List Flights Tool",
        query="Is there any flight from SFO to DEN?",
        output="I will need the date to retrieve relevant flights.",
    ),
    EvalData(
        category="Search Amenities Tool",
        query="Are there any luxury shops?",
        tool_calls=[
            ToolCall(
                name="Search Amenities",
                arguments={
                    "query": "luxury shops",
                },
            ),
        ],
    ),
    EvalData(
        category="Search Amenities Tool",
        query="Where can I get coffee near gate A6?",
        tool_calls=[
            ToolCall(
                name="Search Amenities",
                arguments={
                    "query": "coffee near gate A6",
                },
            ),
        ],
    ),
    EvalData(
        category="Search Policies Tool",
        query="What is the flight cancellation policy?",
        tool_calls=[
            ToolCall(
                name="Search Policies",
                arguments={
                    "query": "flight cancellation policy",
                },
            ),
        ],
    ),
    EvalData(
        category="Search Policies Tool",
        query="How many checked bags can I bring?",
        tool_calls=[
            ToolCall(
                name="Search Policies",
                arguments={
                    "query": "checked baggage allowance",
                },
            ),
        ],
    ),
    EvalData(
        category="Insert Ticket",
        query="I would like to book flight CY 922 departing from SFO on 2025-01-01 at 6:38am.",
        tool_calls=[
            ToolCall(
                name="Insert Ticket",
                arguments={
                    "airline": "CY",
                    "flight_number": "922",
                    "departure_airport": "SFO",
                    "departure_time": "2025-01-01 06:38:00",
                },
            ),
        ],
    ),
    EvalData(
        category="Insert Ticket",
        query="What flights are headed from SFO to DEN on January 1 2025?",
        tool_calls=[
            ToolCall(
                name="List Flights",
                arguments={
                    "departure_airport": "SFO",
                    "arrival_airport": "DEN",
                    "date": "2025-01-01",
                },
            ),
        ],
        reset=False,
    ),
    EvalData(
        category="Insert Ticket",
        query="I would like to book the first flight.",
        tool_calls=[
            ToolCall(
                name="Insert Ticket",
                arguments={
                    "airline": "UA",
                    "flight_number": "1532",
                    "departure_airport": "SFO",
                    "arrival_airport": "DEN",
                    "departure_time": "2025-01-01 05:50:00",
                    "arrival_time": "2025-01-01 09:23:00",
                },
            ),
        ],
    ),
    EvalData(
        category="List Tickets",
        query="Do I have any tickets?",
        tool_calls=[ToolCall(name="List Tickets")],
    ),
    EvalData(
        category="List Tickets",
        query="When is my next flight?",
        tool_calls=[ToolCall(name="List Tickets")],
    ),
    EvalData(
        category="Airline Related Question",
        query="What is Cymbal Air?",
        output="Cymbal Air is a passenger airline offering convenient flights to many cities around the world from its hub in San Francisco.",
    ),
    EvalData(
        category="Airline Related Question",
        query="Where is the hub of cymbal air?",
        output="The hub of Cymbal Air is in San Francisco.",
    ),
    EvalData(
        category="Assistant Related Question",
        query="What can you help me with?",
        output="I can help to book flights and answer a wide range of questions pertaining to travel on Cymbal Air, as well as amenities of San Francisco Airport.",
    ),
    EvalData(
        category="Assistant Related Question",
        query="Can you help me book tickets?",
        output="Yes, I can help with several tools such as search airports, list tickets, book tickets.",
    ),
    EvalData(
        category="Out-Of-Context Question",
        query="Can you help me solve math problems?",
        output="Sorry, I am not given the tools for this.",
    ),
    EvalData(
        category="Out-Of-Context Question",
        query="Who is the CEO of Google?",
        output="Sorry, I am not given the tools for this.",
    ),
    EvalData(
        category="Multitool Selections",
        query="Where can I get a snack near the gate for flight CY 352?",
        tool_calls=[
            ToolCall(
                name="Search Flights By Flight Number",
                arguments={
                    "airline": "CY",
                    "flight_number": "352",
                },
            ),
            ToolCall(
                name="Search Amenities",
                arguments={
                    "query": "snack near gate A2.",
                },
            ),
        ],
    ),
    EvalData(
        category="Multitool Selections",
        query="What are some flights from SFO to Chicago tomorrow?",
        tool_calls=[
            ToolCall(
                name="Search Airport",
                arguments={
                    "city": "Chicago",
                },
            ),
            ToolCall(
                name="List Flights",
                arguments={
                    "departure_airport": "SFO",
                    "arrival_airport": "ORD",
                    "date": f"{get_date(1)}",
                },
            ),
        ],
    ),
]
