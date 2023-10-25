# Copyright 2023 Google LLC
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

import os
from typing import Optional

import google.auth.transport.requests
import google.oauth2.id_token
import requests
from langchain.agents import AgentType, initialize_agent
from langchain.llms.vertexai import VertexAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import StructuredTool, Tool
from pydantic.v1 import BaseModel, Field

DEBUG = bool(os.getenv("DEBUG", default=False))
BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")


# Agent
def init_agent(history):
    """Load an agent executor with tools and LLM"""
    print("Initializing agent..")
    llm = VertexAI(max_output_tokens=512, verbose=DEBUG)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
    )
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=DEBUG,
        memory=memory,
        handle_parsing_errors=True,
        max_iterations=3,
    )
    agent.agent.llm_chain.verbose = DEBUG

    return agent


def get_request(url, params):
    if "http://" in url:
        response = requests.get(
            url,
            params=params,
        )
    else:
        response = requests.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {get_id_token(url)}"},
        )
    return response


def get_id_token(url):
    """Helper Function for authenticated Requests"""
    auth_req = google.auth.transport.requests.Request()
    target_audience = url
    return google.oauth2.id_token.fetch_id_token(auth_req, target_audience)


# Tool Functions
def get_flight(id: int):
    response = get_request(
        f"{BASE_URL}/flights",
        {"id": id},
    )
    if response.status_code != 200:
        return f"Error trying to find flight: {response.text}"

    return response.json()


def list_flights(departure_airport: str, arrival_airport: str, date: str):
    response = get_request(
        f"{BASE_URL}/flights/search",
        {
            "departure_airport": departure_airport,
            "arrival_airport": arrival_airport,
            "date": date,
        },
    )
    if response.status_code != 200:
        return f"Error searching flights: {response.text}"

    return response.json()


def get_amenity(id: int):
    response = get_request(
        f"{BASE_URL}/amenities",
        {"id": id},
    )
    if response.status_code != 200:
        return f"Error trying to find amenity: {response.text}"

    return response.json()


def search_amenities(query: str):
    response = get_request(
        f"{BASE_URL}/amenities/search", {"top_k": "5", "query": query}
    )
    if response.status_code != 200:
        return f"Error searching amenities: {response.text}"

    return response.json()


def get_airport(id: int):
    response = get_request(
        f"{BASE_URL}/airports",
        {"id": id},
    )
    if response.status_code != 200:
        return f"Error trying to find airport: {response.text}"

    return response.json()


# Arg Schema for tools
class IdInput(BaseModel):
    id: int = Field(description="Unique identifier")


class QueryInput(BaseModel):
    query: str = Field(description="Search query")


class ListFlights(BaseModel):
    departure_airport: Optional[str] = Field(
        description="Departure airport 3-letter code"
    )
    arrival_airport: Optional[str] = Field(description="Arrival airport 3-letter code")
    date: str = Field(description="Date of flight departure", default="today")


# Tools for agent
tools = [
    Tool.from_function(
        name="get_flight",  # Name must be unique for tool set
        func=get_flight,
        description="Use this tool to get info for a specific flight. Takes an id and returns info on the flight.",
        args_schema=IdInput,
    ),
    StructuredTool.from_function(
        name="list_flights",
        func=list_flights,
        description="Use this tool to list all flights matching search criteria.",
        args_schema=ListFlights,
    ),
    Tool.from_function(
        name="get_amenity",
        func=get_amenity,
        description="Use this tool to get info for a specific airport amenity. Takes an id and returns info on the amenity. Always use the id from the search_amenities tool.",
        args_schema=IdInput,
    ),
    Tool.from_function(
        name="search_amenities",
        func=search_amenities,
        description="Use this tool to recommended airport amenities at SFO. Returns several amenities that are related to the query. Only recommend amenities that are returned by this query.",
        args_schema=QueryInput,
    ),
    Tool.from_function(
        name="get_airport",
        func=get_airport,
        description="Use this tool to get info for a specific airport. Takes an id and returns info on the airport. Always use the id from the search_airports tool.",
        args_schema=IdInput,
    ),
]
