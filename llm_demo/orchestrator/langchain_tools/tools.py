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


def generate_search_amenities(client: aiohttp.ClientSession):
    async def search_amenities(query: str, open_time: str, open_day: str):
        response = await client.get(
            url=f"{RETRIEVAL_URL}/amenities/search",
            params={
                "top_k": "5",
                "query": query,
                "open_time": open_time,
                "open_day": open_day,
            },
            headers=get_headers(client, RETRIEVAL_URL),
        )

        response = await response.json()
        return response

    return search_amenities


class PolicyQueryInput(BaseModel):
    query: str = Field(description="Search query")


def generate_search_policies(client: aiohttp.ClientSession):
    async def search_policies(query: str):
        response = await client.get(
            url=f"{RETRIEVAL_URL}/policies/search",
            params={"top_k": "5", "query": query},
            headers=get_headers(client, RETRIEVAL_URL),
        )

        response = await response.json()
        return response

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
    seat_row: Optional[int] = Field(
        description="A number between 1 to 33 for the seat row",
    )
    seat_letter: Optional[str] = Field(
        description="A single letter between A, B, C, D, E and F",
    )


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


async def insert_ticket(client: aiohttp.ClientSession, params: str):
    ticket_info = json.loads(params)
    response = await client.post(
        url=f"{RETRIEVAL_URL}/tickets/insert",
        params={
            "airline": ticket_info.get("airline"),
            "flight_number": ticket_info.get("flight_number"),
            "departure_airport": ticket_info.get("departure_airport"),
            "arrival_airport": ticket_info.get("arrival_airport"),
            "departure_time": ticket_info.get("departure_time").replace("T", " "),
            "arrival_time": ticket_info.get("arrival_time").replace("T", " "),
            "seat_row": ticket_info.get("seat_row"),
            "seat_letter": ticket_info.get("seat_letter"),
        },
        headers=get_headers(client, RETRIEVAL_URL),
    )
    response = await response.json()
    return response


class NL2QueryInput(BaseModel):
    query: str = Field(description="Search query")


def generate_nl2query(client: aiohttp.ClientSession, user_email: str):
    async def nl2query(query: str):
        response = await client.get(
            url=f"{NL2QUERY_URL}/run_query",
            params={"query": query, "user_email": user_email},
            headers=get_headers(client, NL2QUERY_URL),
        )

        response_json = await response.json()

        if response_json["is_clear"] is True:
            return response_json["results"]
        else:
            return f"The previous information provided is insufficient. We have a followup question for the user: {response_json.followup_question}"

    return nl2query


# Tools for agent
async def initialize_tools(client: aiohttp.ClientSession, user_email: str):
    return [
        StructuredTool.from_function(
            coroutine=generate_search_amenities(client),
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
            coroutine=generate_search_policies(client),
            name="Search Policies",
            description="""
						Use this tool to search for cymbal air passenger policy.
						Policy that are listed is unchangeable.
						You will not answer any questions outside of the policy given.
						Policy includes information on ticket purchase and changes, baggage, check-in and boarding, special assistance, overbooking, flight delays and cancellations.
                        """,
            args_schema=PolicyQueryInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_insert_ticket(client),
            name="Insert Ticket",
            description="""
                        Use this tool to book a flight ticket for the user.
                        Example:
                        {{
                            "airline": "AA",
                            "flight_number": "452",
                            "departure_airport": "LAX",
                            "arrival_airport": "SFO",
                            "departure_time": "2024-01-01 05:50:00",
                            "arrival_time": "2024-01-01 09:23:00",
                            "seat_row": null,
                            "seat_letter": null
                        }}
                        Example:
                        {{
                            "airline": "UA",
                            "flight_number": "1532",
                            "departure_airport": "SFO",
                            "arrival_airport": "DEN",
                            "departure_time": "2024-01-08 05:50:00",
                            "arrival_time": "2024-01-08 09:23:00",
                            "seat_row": null,
                            "seat_letter": null,
                        }}
                        Example:
                        {{
                            "airline": "OO",
                            "flight_number": "6307",
                            "departure_airport": "SFO",
                            "arrival_airport": "MSP",
                            "departure_time": "2024-10-28 20:13:00",
                            "arrival_time": "2024-10-28 21:07:00",
                            "seat_row": null,
                            "seat_letter": null,
                        }}
                        Example with user requesting to book seat 24B:
                        {{
                            "airline": "AA",
                            "flight_number": "452",
                            "departure_airport": "LAX",
                            "arrival_airport": "SFO",
                            "departure_time": "2024-01-01 05:50:00",
                            "arrival_time": "2024-01-01 09:23:00",
                            "seat_row": "24",
                            "seat_letter": "B",
                        }}
                        """,
            args_schema=TicketInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_nl2query(client, user_email),
            name="General Flight and Airport Information",
            description="""
                        Use this tool to query information from the database. The database have information on flights, airports, and tickets.
                        Send user query in natural language to the tool.
                        If a follow up question is used, include the previous user query in the current query.

                        Example of information that will be able to retrieved from the tool includes:
                        - Listing flights that are available from an airport, or to an airport, on a specific date.
                        - Get information for a specific flight using airline code or flight number.
                        - List information of an airport. This will provide airport information such as airport's name, iata code, etc.
                        """,
            args_schema=NL2QueryInput,
        ),
    ]


def get_confirmation_needing_tools():
    return ["Insert Ticket"]
