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

# from langchain.agents.mrkl.base import ZeroShotAgent
# from langchain.llms import VertexAI
from langchain.chat_models.vertexai import ChatVertexAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import StructuredTool, Tool
from pydantic.v1 import BaseModel, Field

DEBUG = bool(os.getenv("DEBUG", default=False))
BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")


def init_agent(history):
    """Load an agent executor with tools and LLM"""
    print("Initializing agent..")
    llm = ChatVertexAI(max_output_tokens=512, verbose=DEBUG)
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
    )
    agent.agent.llm_chain.verbose = DEBUG
    # Change the prompt
    # new_prompt = ZeroShotAgent.create_prompt(tools=tools, prefix=prefix, suffix=suffix)
    # agent.agent.llm_chain.prompt = new_prompt
    return agent


def get_id_token():
    auth_req = google.auth.transport.requests.Request()
    target_audience = BASE_URL

    return google.oauth2.id_token.fetch_id_token(auth_req, target_audience)


def get_flight(id: int):
    # response = requests.get(
    #     f"{BASE_URL}/flights/{id}",
    #     headers={"Authorization": f"Bearer {get_id_token()}"},
    # )

    # if response.status_code != 200:
    #     return f"Error trying to find flight: {response.text}"

    # return response.json()

    return {
        "id": id,
        "departure_time": "11am",
        "departure_airport": "SFO",
        "depature_gate": "A13",
        "arrival_gate": "N2",
        "arrival_time": "1pm",
        "arrival_airport": "SEA",
        "boarding_time": "10:45am",
        "airline": "Alaska Airlines",
    }


def list_flights(departure_airport: str, arrival_airport: str, date: str):
    # params = {"top_k": "5", "query": desc}

    # response = requests.get(
    #     f"{BASE_URL}/flights/search",
    #     params,
    #     headers={"Authorization": f"Bearer {get_id_token()}"},
    # )
    # if response.status_code != 200:
    #     return f"Error trying to find flight: {response.text}"

    # return response.json()
    return [
        {
            "id": 405,
            "departure_time": "11am",
            "departure_airport": "SFO",
            "depatrue_gate": "A13",
            "arrival_gate": "N2",
            "arrival_time": "1pm",
            "arrival_airport": "SEA",
            "boarding_time": "10:45am",
            "airline": "Alaska Airlines",
        },
        {
            "id": 433,
            "departure_time": "10am",
            "departure_airport": "SFO",
            "depatrue_gate": "A3",
            "arrival_gate": "N12",
            "arrival_time": "1:20pm",
            "arrival_airport": "SEA",
            "boarding_time": "10:30am",
            "airline": "Alaska Airlines",
        },
    ]


def get_amenity(id: int):
    response = requests.get(
        f"{BASE_URL}/amenities",
        params={"id": id},
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )

    if response.status_code != 200:
        return f"Error trying to find flight: {response.text}"

    return response.json()
    # return {
    #     "id": id,
    #     "name": "Hudson Bay",
    #     "description": "Get your airport snalcs",
    #     "location": "Near Gate A13",
    #     "terminal": "Terminal 3",
    #     "category": "shop",
    #     "hours": "Sunday-Saturday 7:00 am-11:00 pm",
    #     "content": "This amenity is a <category>. <description>",
    # }


def search_amenities(query: str):
    params = {"top_k": "5", "query": query}

    response = requests.get(
        f"{BASE_URL}/amenities/search",
        params,
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )
    if response.status_code != 200:
        return f"Error trying to find flight: {response.text}"

    return response.json()
    # return [
    #     {
    #         "id": 1,
    #         "name": "Hudson Bay",
    #         "description": "Get your airport snacks",
    #         "location": "Near Gate A13",
    #         "terminal": "Terminal 3",
    #         "category": "shop",
    #         "hours": "Sunday-Saturday 7:00 am-11:00 pm",
    #         "content": "This amenity is a <category>. <description>",
    #     },
    #     {
    #         "id": 2,
    #         "name": "Beechers",
    #         "description": "Get your airport snacks",
    #         "location": "Near Gate B3",
    #         "terminal": "Terminal 3",
    #         "category": "restaurant",
    #         "hours": "Sunday-Saturday 7:00 am-11:00 pm",
    #         "content": "This amenity is a <category>. <description>",
    #     },
    # ]


def get_airport(id: int):
    # response = requests.get(
    #     f"{BASE_URL}/airports/{id}",
    #     headers={"Authorization": f"Bearer {get_id_token()}"},
    # )

    # if response.status_code != 200:
    #     return f"Error trying to find airport: {response.text}"

    # return response.json()
    return {
        "id": id,
        "iata": "SFO",
        "name": "San Francisco International Airport",
        "city": "San Francisco",
        "country": "United States",
        "content": "The San Francisco International Airport is located in San Francisco, United States.",
    }


def search_airports(query: str):
    # params = {"top_k": "5", "query": desc}

    # response = requests.get(
    #     f"{BASE_URL}/airports/semantic_lookup",
    #     params,
    #     headers={"Authorization": f"Bearer {get_id_token()}"},
    # )
    # if response.status_code != 200:
    #     return f"Error trying to find flight: {response.text}"

    # return response.json()
    return [
        {
            "id": 1,
            "iata": "SFO",
            "name": "San Francisco International Airport",
            "city": "San Francisco",
            "country": "United States",
            "content": "The San Francisco International Airport is located in San Francisco, United States.",
        },
        {
            "id": 2,
            "iata": "OAK",
            "name": "Oakland International Airport",
            "city": "Oakland",
            "country": "United States",
            "content": "The Oakland International Airport is located in Oakland, United States.",
        },
    ]


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
        description="Use this tool to get info for a specific airport amenity. Takes an id and returns info on the amenity.",
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
        description="Use this tool to get info for a specific airport. Takes an id and returns info on the airport.",
        args_schema=IdInput,
    ),
    Tool.from_function(
        name="search_airports",
        func=search_airports,
        description="Use this tool to search for airports and information.",
        args_schema=QueryInput,
    ),
]
