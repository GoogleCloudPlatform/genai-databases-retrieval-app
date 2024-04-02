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

import json
import os
from datetime import datetime
from typing import Dict, Optional

import aiohttp
import google.oauth2.id_token  # type: ignore
from google.auth import compute_engine  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from langchain.agents.agent import ExceptionTool  # type: ignore
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field

from .helpers import ToolTrace

RETRIEVAL_URL = os.getenv("RETRIEVAL_URL", default="http://127.0.0.1:8080")
NL2QUERY_URL = os.getenv("NL2QUERY_URL", default="http://127.0.0.1:8084")
CREDENTIALS = {}


def filter_none_values(params: dict) -> dict:
    return {key: value for key, value in params.items() if value is not None}


def get_id_token(base_url: str):
    global CREDENTIALS
    if base_url not in CREDENTIALS:
        CREDENTIALS[base_url], _ = google.auth.default()
        if not hasattr(CREDENTIALS[base_url], "id_token"):
            # Use Compute Engine default credential
            CREDENTIALS[base_url] = compute_engine.IDTokenCredentials(
                request=Request(),
                target_audience=base_url,
                use_metadata_identity_endpoint=True,
            )
    if not CREDENTIALS[base_url].valid:
        CREDENTIALS[base_url].refresh(Request())
    if hasattr(CREDENTIALS[base_url], "id_token"):
        return CREDENTIALS[base_url].id_token
    else:
        return CREDENTIALS[base_url].token


def get_headers(client: aiohttp.ClientSession, base_url: str):
    """Helper method to generate ID tokens for authenticated requests"""
    headers = client.headers
    if not "http://" in base_url:
        # Append ID Token to make authenticated requests to Cloud Run services
        headers["Authorization"] = f"Bearer {get_id_token(base_url)}"
    return headers


# Tools
class AmenityQueryInput(BaseModel):
    query: str = Field(description="Search query")
    open_time: Optional[str] = Field(
        description="Time for filtering amenities by operating hours"
    )
    open_day: Optional[str] = Field(
        description="Day of the week for filtering amenities by operating hours"
    )


def generate_search_amenities(client: aiohttp.ClientSession, tool_trace: ToolTrace):
    async def search_amenities(query: str, open_time: str, open_day: str):
        params = {
            "top_k": "5",
            "query": query,
            "open_time": open_time,
            "open_day": open_day,
        }
        response = await client.get(
            url=f"{RETRIEVAL_URL}/amenities/search",
            params=filter_none_values(params),
            headers=get_headers(client, RETRIEVAL_URL),
        )

        response_json = await response.json()
        if response_json.get("trace"):
            tool_trace.add_message(response_json.get("trace"))
        return response_json.get("result")

    return search_amenities


class PolicyQueryInput(BaseModel):
    query: str = Field(description="Search query")


def generate_search_policies(client: aiohttp.ClientSession, tool_trace: ToolTrace):
    async def search_policies(query: str):
        response = await client.get(
            url=f"{RETRIEVAL_URL}/policies/search",
            params={"top_k": "5", "query": query},
            headers=get_headers(client, RETRIEVAL_URL),
        )

        response_json = await response.json()

        if response_json.get("trace"):
            tool_trace.add_message(response_json.get("trace"))
        return response_json.get("result")

    return search_policies


class TicketInput(BaseModel):
    airline: str = Field(description="Airline unique 2 letter identifier")
    flight_number: str = Field(description="1 to 4 digit number")
    departure_airport: str = Field(
        description="Departure airport 3-letter code",
    )
    arrival_airport: str = Field(description="Arrival airport 3-letter code")
    departure_time: datetime = Field(description="Flight departure datetime")
    arrival_time: datetime = Field(description="Flight arrival datetime")
    seat_row: int = Field(description="A number between 1 to 33 for the seat row")
    seat_letter: str = Field(description="A single letter between A, B, C, D, E and F")


def generate_insert_ticket(client: aiohttp.ClientSession):
    async def insert_ticket(
        airline: str,
        flight_number: str,
        departure_airport: str,
        arrival_airport: str,
        departure_time: datetime,
        arrival_time: datetime,
        seat_row: int,
        seat_letter: str,
    ):
        return f"Booking ticket on {airline} {flight_number}"

    return insert_ticket


async def insert_ticket(
    client: aiohttp.ClientSession, params: str, tool_trace: ToolTrace
):
    ticket_info = json.loads(params)
    response = await client.post(
        url=f"{RETRIEVAL_URL}/tickets/insert",
        params=filter_none_values(
            {
                "airline": ticket_info.get("airline"),
                "flight_number": ticket_info.get("flight_number"),
                "departure_airport": ticket_info.get("departure_airport"),
                "arrival_airport": ticket_info.get("arrival_airport"),
                "departure_time": ticket_info.get("departure_time").replace("T", " "),
                "arrival_time": ticket_info.get("arrival_time").replace("T", " "),
                "seat_row": ticket_info.get("seat_row"),
                "seat_letter": ticket_info.get("seat_letter"),
            }
        ),
        headers=get_headers(client, RETRIEVAL_URL),
    )
    response_json = await response.json()

    if response_json.get("trace"):
        tool_trace.add_message(response_json.get("trace"))
    return response_json.get("result")


class NL2QueryInput(BaseModel):
    query: str = Field(description="Search query")


def generate_nl2query(
    client: aiohttp.ClientSession, user_email: str, tool_trace: ToolTrace
):
    async def nl2query(query: str):
        response = await client.get(
            url=f"{NL2QUERY_URL}/run_query",
            params={"query": query, "user_email": user_email},
            headers=get_headers(client, NL2QUERY_URL),
        )

        response_json = await response.json()

        if response_json.get("trace"):
            tool_trace.add_message(response_json.get("trace"))
        if response_json.get("is_clear") is True:
            return f"These are the matching queries: {response_json.get('results')}"
        else:
            return f"The previous information provided is insufficient. We have a followup question for the user: {response_json.get('followup_question')}"

    return nl2query


# Tools for agent
async def initialize_tools(
    client: aiohttp.ClientSession, user_email: str, tool_trace: ToolTrace
):
    return [
        StructuredTool.from_function(
            coroutine=generate_search_amenities(client, tool_trace),
            name="Search Amenities",
            description="""
    Use this tool to search amenities by name or to recommended airport amenities at SFO.
    If user provides flight info, use 'Search Flights by Flight Number'
    first to get gate info and location.

    User can also provide open_time and open_day to check amenities opening hour.
    Open_time is provided in the HH:MM:SS format.
    Open_day is one of days of the week (for example: sunday, monday, etc.). Convert terms like today to today's day.
    If open_time is provided, open_day MUST be provided as well. If open_time is provided without open_day, default open_day to today's day. If open_day is provided without open_time, default open_time to current time.

    Only recommend amenities that are returned by this query.
    Find amenities close to the user by matching the terminal and then comparing
    the gate numbers. Gate number iterate by letter and number, example A1 A2 A3
    B1 B2 B3 C1 C2 C3. Gate A3 is close to A2 and B1.

    Example:
    {{
        "query": "A burger place",
        "open_time": null,
        "open_day": null,
    }}
    Example:
    {{
        "query": "Shop for luxury goods",
        "open_time": "10:00:00",
        "open_day": "wednesday",
    }}
                        """,
            args_schema=AmenityQueryInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_search_policies(client, tool_trace),
            name="Search Policies",
            description="""
    Use this tool to search for Cymbal Air policies including ticket purchase and change fees, baggage restriction, 
    checkin and boarding procedures, special assistance, overbooking, flight delays and cancellations.
    Policy that are listed is unchangeable.
    You will not answer any questions outside of the policy given.

    Example: Is there a fee to switch to a later flight?
    {{
        "query": "ticket change fees"
    }}
                        """,
            args_schema=PolicyQueryInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_insert_ticket(client),
            name="Insert Ticket",
            description="""
    Use this tool to book a flight ticket for the user. Make sure to include all necessary arguments: airline, flight_number, departure_airport, 
    arrival_airport, departure_time, arrival_time, seat_row and seat_letter.  If any of these are missing, ask the user for additional information.

    Example of user booking on American Airlines flight 452 from LAX to SFO on January 1st, 2024 with seat 10A:
    {{
        "airline": "AA",
        "flight_number": "452",
        "departure_airport": "LAX",
        "arrival_airport": "SFO",
        "departure_time": "2024-01-01 05:50:00",
        "arrival_time": "2024-01-01 09:23:00",
        "seat_row": "10",
        "seat_letter": "A",
    }}
                        """,
            args_schema=TicketInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_nl2query(client, user_email, tool_trace),
            name="General Flight and Airport Information",
            description="""
    Use this tool to query generic information about flights, tickets, seats and airports.
    
    Do not assume any information and do not omit any information! 
    It is important to include as much detail from the user's original query as possible (such as adjectives). See additional examples below for the correct way to respond. 
    If a follow up question is used, include the previous user query in the current query.

    Example with user asking about flights to New York (without additional context):
    Human: "Are there any flights to New York?"
    {{
        "query": "List flights to New York."
    }}
    
    Example with user asking about flights for tomorrow:
    Human: "Are there any flights from SFO to DEN tomorrow?"
    {{
        "query": "List flights from SFO to DEN tomorrow",
    }}
    
    Example with user asking about the next flight to New York City for today:
    Human: "What is the next flight to New York City today?"
    {{
        "query": "List next flight from SFO to New York City today",
    }}
    or
    Human: "What time are some later Cymbal Air flights to New York today?"
    {{
        "query": "List later Cymbal Air flights to New York today",
    }}
    
    Example with user asking about flights for tomorrow with airline preferences:
    Human: "I would like to look for cymbal air flights to SEA tomorrow"
    {{
        "query": "List flights from SFO to SEA tomorrow on Cymbal Air",
    }}

    Example with user asking about seats available on a flight this evening to Boston
    Human: "Are there any flights to Boston tonight?"
    AI: "United flight 833 departs SFO at 9:15pm and lands tomorrow morning at Boston Logan at 6:08 am"
    Human: "Are there any window seats in premium economy?"
    {{
        "query": "List available window seats in premium economy on UA 833 departing tonight at 9:15pm",
    }}

    - Get information for a specific flight using airline code or flight number.

    - List information of an airport. This will provide airport information such as airport's name, iata code, etc.

    - List seats that are available on a specific flight. Information such as specific seats type (for example, Economy, Premium Economy, Business Class, and First Class) or seats location (for example, aisle, middle, window) needs to be included if user provides them.
    Example with user asking about business class seats of a specific flight:
    Human: "What are some available business class seats on CY 123 tomorrow?"
    {{
        "query": "List available business class seats on CY 123 tomorrow.",
    }}
    Example with user asking for a good seat:
    Human: "Find a good seat on CY 123 on April 7th, 2024."
    {{
        "query": "List good seats that are available on flight CY 123 on 2024-04-07.",
    }}
    Example with user asking for a seat with leg room:
    Human: "Is there a seat with legroom on the next flight to Seattle today?"
    {{
        "query": "List seats with legroom on the next flight to Seattle today"
    }}
    Example with user asking seats of a specific flight with seat type preferences:
    Human: "Is there any first class seats on flight xx  xxxx?"
    {{
        "query": "List seats that are available on flight XX  XXXX in first class.",
    }}
    Example with user asking seats of a specific flight with seat type and seat location preferences:
    Human: "I would like economy seats that are either window or aisle."
    {{
        "query": "List seats that are available on flight XX  XXXX in economy class and window or aisle seat",
    }}

    - List tickets that have been purchased by this user
    Example with user asking information regarding their ticket or their flight:
    Human: "What time is my flight?"
    {{
        "query": "list flight for this user.",
    }}

    Example with user asking for specific information about an upcoming reservation:
    Human: "Which seat am I in for my flight to Boston?"
    {{
        "query": "list tickets including seat assignment for this user's next flight to Boston.",
    }}
                        """,
            args_schema=NL2QueryInput,
        ),
    ]


def get_confirmation_needing_tools():
    return ["Insert Ticket"]
