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
from datetime import datetime
from typing import Optional

import aiohttp
import google.oauth2.id_token  # type: ignore
from google.auth import compute_engine  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from langchain.agents.agent import ExceptionTool  # type: ignore
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field

BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
CREDENTIALS = None


def filter_none_values(params: dict) -> dict:
    return {key: value for key, value in params.items() if value is not None}


def get_id_token():
    global CREDENTIALS
    if CREDENTIALS is None:
        CREDENTIALS, _ = google.auth.default()
        if not hasattr(CREDENTIALS, "id_token"):
            # Use Compute Engine default credential
            CREDENTIALS = compute_engine.IDTokenCredentials(
                request=Request(),
                target_audience=BASE_URL,
                use_metadata_identity_endpoint=True,
            )
    if not CREDENTIALS.valid:
        CREDENTIALS.refresh(Request())
    if hasattr(CREDENTIALS, "id_token"):
        return CREDENTIALS.id_token
    else:
        return CREDENTIALS.token


def get_headers(client: aiohttp.ClientSession):
    """Helper method to generate ID tokens for authenticated requests"""
    headers = client.headers
    if not "http://" in BASE_URL:
        # Append ID Token to make authenticated requests to Cloud Run services
        headers["Authorization"] = f"Bearer {get_id_token()}"
    return headers


# Tools
class AirportSearchInput(BaseModel):
    country: Optional[str] = Field(description="Country")
    city: Optional[str] = Field(description="City")
    name: Optional[str] = Field(description="Airport name")


def generate_search_airports(client: aiohttp.ClientSession):
    async def search_airports(country: str, city: str, name: str):
        params = {
            "country": country,
            "city": city,
            "name": name,
        }
        response = await client.get(
            url=f"{BASE_URL}/airports/search",
            params=filter_none_values(params),
            headers=get_headers(client),
        )

        num = 2
        response_json = await response.json()
        if len(response_json) < 1:
            return "There are no airports matching that query. Let the user know there are no results."
        elif len(response_json) > num:
            return (
                f"There are {len(response_json)} airports matching that query. Here are the first {num} results:\n"
                + " ".join([f"{response_json[i]}" for i in range(num)])
            )
        else:
            return "\n".join([f"{r}" for r in response_json])

    return search_airports


class FlightNumberInput(BaseModel):
    airline: str = Field(description="Airline unique 2 letter identifier")
    flight_number: str = Field(description="1 to 4 digit number")


def generate_search_flights_by_number(client: aiohttp.ClientSession):
    async def search_flights_by_number(airline: str, flight_number: str):
        response = await client.get(
            url=f"{BASE_URL}/flights/search",
            params={"airline": airline, "flight_number": flight_number},
            headers=get_headers(client),
        )

        return await response.json()

    return search_flights_by_number


class ListFlights(BaseModel):
    departure_airport: Optional[str] = Field(
        description="Departure airport 3-letter code",
    )
    arrival_airport: Optional[str] = Field(description="Arrival airport 3-letter code")
    date: str = Field(description="Date of flight departure")


def generate_list_flights(client: aiohttp.ClientSession):
    async def list_flights(
        departure_airport: str,
        arrival_airport: str,
        date: str,
    ):
        params = {
            "departure_airport": departure_airport,
            "arrival_airport": arrival_airport,
            "date": date,
        }
        response = await client.get(
            url=f"{BASE_URL}/flights/search",
            params=filter_none_values(params),
            headers=get_headers(client),
        )

        num = 2
        response_json = await response.json()
        if len(response_json) < 1:
            return "There are no flights matching that query. Let the user know there are no results."
        elif len(response_json) > num:
            return (
                f"There are {len(response_json)} flights matching that query. Here are the first {num} results:\n"
                + " ".join([f"{response_json[i]}" for i in range(num)])
            )
        else:
            return "\n".join([f"{r}" for r in response_json])

    return list_flights


class QueryInput(BaseModel):
    query: str = Field(description="Search query")


def generate_search_amenities(client: aiohttp.ClientSession):
    async def search_amenities(query: str):
        response = await client.get(
            url=f"{BASE_URL}/amenities/search",
            params={"top_k": "5", "query": query},
            headers=get_headers(client),
        )

        response = await response.json()
        return response

    return search_amenities


class TicketInput(BaseModel):
    airline: str = Field(description="Airline unique 2 letter identifier")
    flight_number: str = Field(description="1 to 4 digit number")
    departure_airport: str = Field(
        description="Departure airport 3-letter code",
    )
    arrival_airport: str = Field(description="Arrival airport 3-letter code")
    departure_time: datetime = Field(description="Flight departure datetime")
    arrival_time: datetime = Field(description="Flight arrival datetime")


def generate_insert_ticket(client: aiohttp.ClientSession):
    async def insert_ticket(
        airline: str,
        flight_number: str,
        departure_airport: str,
        arrival_airport: str,
        departure_time: datetime,
        arrival_time: datetime,
    ):
        response = await client.post(
            url=f"{BASE_URL}/tickets/insert",
            params={
                "airline": airline,
                "flight_number": flight_number,
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "departure_time": departure_time.strftime("%Y-%m-%d %H:%M:%S"),
                "arrival_time": arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            headers=get_headers(client),
        )

        response = await response.json()
        return response

    return insert_ticket


def generate_list_tickets(client: aiohttp.ClientSession):
    async def list_tickets():
        response = await client.get(
            url=f"{BASE_URL}/tickets/list",
            headers=get_headers(client),
        )

        response = await response.json()
        return response

    return list_tickets


# Tools for agent
async def initialize_tools(client: aiohttp.ClientSession):
    return [
        StructuredTool.from_function(
            coroutine=generate_search_airports(client),
            name="Search Airport",
            description="""
                        Use this tool to list all airports matching search criteria.
                        Takes at least one of country, city, name, or all and returns all matching airports.
                        The agent can decide to return the results directly to the user.
                        Input of this tool must be in JSON format and include all three inputs - country, city, name.
                        Example:
                        {{
                            "country": "United States",
                            "city": "San Francisco",
                            "name": null
                        }}
                        Example:
                        {{
                            "country": null,
                            "city": "Goroka",
                            "name": "Goroka"
                        }}
                        Example:
                        {{
                            "country": "Mexico",
                            "city": null,
                            "name": null
                        }}
                        """,
            args_schema=AirportSearchInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_search_flights_by_number(client),
            name="Search Flights By Flight Number",
            description="""
                        Use this tool to get information for a specific flight.
                        Takes an airline code and flight number and returns info on the flight.
                        Do NOT use this tool with a flight id. Do NOT guess an airline code or flight number.
                        A airline code is a code for an airline service consisting of two-character
                        airline designator and followed by flight number, which is 1 to 4 digit number.
                        For example, if given CY 0123, the airline is "CY", and flight_number is "123".
                        Another example for this is DL 1234, the airline is "DL", and flight_number is "1234".
                        If the tool returns more than one option choose the date closes to today.
                        Example:
                        {{
                            "airline": "CY",
                            "flight_number": "888",
                        }}
                        Example:
                        {{
                            "airline": "DL",
                            "flight_number": "1234",
                        }}
                        """,
            args_schema=FlightNumberInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_list_flights(client),
            name="List Flights",
            description="""
                        Use this tool to list flights information matching search criteria.
                        Takes an arrival airport, a departure airport, or both, filters by date and returns all matching flights.
                        If 3-letter iata code is not provided for departure_airport or arrival_airport, use search airport tools to get iata code information.
                        Do NOT guess a date, ask user for date input if it is not given. Date must be in the following format: YYYY-MM-DD.
                        The agent can decide to return the results directly to the user.
                        Input of this tool must be in JSON format and include all three inputs - arrival_airport, departure_airport, and date.
                        Example:
                        {{
                            "departure_airport": "SFO",
                            "arrival_airport": null,
                            "date": 2023-10-30"
                        }}
                        Example:
                        {{
                            "departure_airport": "SFO",
                            "arrival_airport": "SEA",
                            "date": "2023-11-01"
                        }}
                        Example:
                        {{
                            "departure_airport": null,
                            "arrival_airport": "SFO",
                            "date": "2023-01-01"
                        }}
                        """,
            args_schema=ListFlights,
        ),
        StructuredTool.from_function(
            coroutine=generate_search_amenities(client),
            name="Search Amenities",
            description="""
                        Use this tool to search amenities by name or to recommended airport amenities at SFO.
                        If user provides flight info, use 'Search Flights by Flight Number'
                        first to get gate info and location.
                        Only recommend amenities that are returned by this query.
                        Find amenities close to the user by matching the terminal and then comparing
                        the gate numbers. Gate number iterate by letter and number, example A1 A2 A3
                        B1 B2 B3 C1 C2 C3. Gate A3 is close to A2 and B1.
                        """,
            args_schema=QueryInput,
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
                            "arrival_time": "2024-01-01 09:23:00"
                        }}
                        Example:
                        {{
                            "airline": "UA",
                            "flight_number": "1532",
                            "departure_airport": "SFO",
                            "arrival_airport": "DEN",
                            "departure_time": "2024-01-08 05:50:00",
                            "arrival_time": "2024-01-08 09:23:00"
                        }}
                        Example:
                        {{
                            "airline": "OO",
                            "flight_number": "6307",
                            "departure_airport": "SFO",
                            "arrival_airport": "MSP",
                            "departure_time": "2024-10-28 20:13:00",
                            "arrival_time": "2024-10-28 21:07:00"
                        }}
                        """,
            args_schema=TicketInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_list_tickets(client),
            name="List Tickets",
            description="""
                        Use this tool to list a user's flight tickets.
                        Takes no input and returns a list of current user's flight tickets.
                        Input is always empty JSON blob. Example: {{}}
                        """,
        ),
    ]
