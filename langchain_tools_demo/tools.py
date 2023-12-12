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
from datetime import date, timedelta
from typing import Optional

import aiohttp
import dateutil.parser as dparser
import google.auth.transport.requests  # type: ignore
import google.oauth2.id_token  # type: ignore
from langchain.tools import StructuredTool, tool
from pydantic.v1 import BaseModel, Field

BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
session = None


# create a new client session
async def get_session():
    if session is None:
        client_session = aiohttp.ClientSession()
    return client_session


# Helper functions
async def get_request(url: str, params: dict) -> aiohttp.ClientResponse:
    """Helper method to make backend requests"""
    session = await get_session()
    if "http://" in url:
        response = await session.get(
            url,
            params=params,
        )
        return response
    else:
        # Append ID Token to make authenticated requests to Cloud Run services
        response = await session.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {get_id_token(url)}"},
        )
        return response


def get_id_token(url: str) -> str:
    """Helper method to generate ID tokens for authenticated requests"""
    # Use Application Default Credentials on Cloud Run
    if os.getenv("K_SERVICE"):
        auth_req = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(auth_req, url)
    else:
        # Use gcloud credentials locally
        import subprocess

        return (
            subprocess.run(
                ["gcloud", "auth", "print-identity-token"],
                stdout=subprocess.PIPE,
                check=True,
            )
            .stdout.strip()
            .decode()
        )


def convert_date(date_string: str) -> str:
    """Convert date into appropriate date string"""
    if date_string == "tomorrow":
        converted = date.today() + timedelta(1)
    elif date_string == "yesterday":
        converted = date.today() - timedelta(1)
    elif date_string != "null" and date_string != "today" and date_string is not None:
        converted = dparser.parse(date_string, fuzzy=True).date()
    else:
        converted = date.today()

    return converted.strftime("%Y-%m-%d")


# Tools
class AirportIdInput(BaseModel):
    id: int = Field(description="Unique identifier")


async def get_airport(id: int):
    """
    Use this tool to get info for a specific airport.
    Do NOT guess an airport id.
    Takes an id and returns info on the airport.
    """
    response = await get_request(
        f"{BASE_URL}/airports",
        {"id": id},
    )
    if response.status != 200:
        return f"Error trying to find airport: {response}"

    return await response.json()


class FlightIdInput(BaseModel):
    id: int = Field(description="Unique identifier")


async def get_flight(id: int):
    """
    Use this tool to get info for a specific flight.
    Takes an id and returns info on the flight.
    Do NOT use this tool if you have a flight number.
    Do NOT guess an airline or flight number.
    """
    response = await get_request(
        f"{BASE_URL}/flights",
        {"flight_id": id},
    )
    if response.status != 200:
        return f"Error trying to find flight: {response}"

    return await response.json()


class FlightNumberInput(BaseModel):
    airline: str = Field(description="Airline unique 2 letter identifier")
    flight_number: str = Field(description="1 to 4 digit number")


async def search_flights_by_number(airline: str, flight_number: str):
    """
    Use this tool to get info for a specific flight. Do NOT use this tool with a flight id.
    Takes an airline and flight number and returns info on the flight.
    Do NOT guess an airline or flight number.
    A flight number is a code for an airline service consisting of two-character
    airline designator and a 1 to 4 digit number ex. OO123, DL 1234, BA 405, AS 3452.
    If the tool returns more than one option choose the date closes to today.
    """
    response = await get_request(
        f"{BASE_URL}/flights/search",
        {"airline": airline, "flight_number": flight_number},
    )
    if response.status != 200:
        return f"Error trying to find flight: {response}"

    return await response.json()


class ListFlights(BaseModel):
    departure_airport: Optional[str] = Field(
        description="Departure airport 3-letter code",
    )
    arrival_airport: Optional[str] = Field(description="Arrival airport 3-letter code")
    date: Optional[str] = Field(description="Date of flight departure")


async def list_flights(departure_airport: str, arrival_airport: str, date: str):
    """
    Use this tool to list all flights matching search criteria.
    Takes an arrival airport, a departure airport, or both, filters by date and returns all matching flights.
    The agent can decide to return the results directly to the user.
    Input of this tool must be in JSON format and include all three inputs - arrival_airport, departure_airport, and date.
    Example:
    {{
        "departure_airport": "SFO",
        "arrival_airport": null,
        "date": null
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
    """
    departure_airport = "SFO"
    arrival_airport = "LAX"
    response = await get_request(
        f"{BASE_URL}/flights/search",
        {
            "departure_airport": departure_airport,
            "arrival_airport": arrival_airport,
            "date": date,
        },
    )
    if response.status != 200:
        return f"Error searching flights: {response}"

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


# Amenities
class AmenityIdInput(BaseModel):
    id: int = Field(description="Unique identifier")


@tool("Get Amenity", args_schema=AmenityIdInput)
async def get_amenity(id: int):
    """
    Use this tool to get info for a specific airport amenity.
    Takes an id and returns info on the amenity.
    Do NOT guess an amenity id. Use Search Amenities to search by name.
    Always use the id from the search_amenities tool.
    """
    response = await get_request(
        f"{BASE_URL}/amenities",
        {"id": id},
    )
    if response.status != 200:
        return f"Error trying to find amenity: {response}"

    return await response.json()


class QueryInput(BaseModel):
    query: str = Field(description="Search query")


async def search_amenities(query: str):
    """
    Use this tool to search amenities by name or to recommended airport amenities at SFO.
    If user provides flight info, use 'Get Flight' and 'Get Flights by Number'
    first to get gate info and location.
    Only recommend amenities that are returned by this query.
    Find amenities close to the user by matching the terminal and then comparing
    the gate numbers. Gate number iterate by letter and number, example A1 A2 A3
    B1 B2 B3 C1 C2 C3. Gate A3 is close to A2 and B1.
    """
    response = await get_request(
        f"{BASE_URL}/amenities/search", {"top_k": "5", "query": query}
    )
    if response.status != 200:
        return f"Error searching amenities: {response}"

    response = await response.json()
    print("printing response")
    print(response)
    return response


# Tools for agent
def initialize_tools():
    return [
        StructuredTool.from_function(
            coroutine=get_airport,
            name="Get Airport",
            description="""Use this tool to get info for a specific airport.
                            Do NOT guess an airport id.
                            Takes an id and returns info on the airport.
                        """,
            args_schema=AirportIdInput,
        ),
        StructuredTool.from_function(
            coroutine=get_flight,
            name="Get Flight",
            description="""
                        Use this tool to get info for a specific flight.
                        Takes an id and returns info on the flight.
                        A flight number is a code for an airline service consisting of two-character
                        airline designator and a 1 to 4 digit number ex. OO123, DL 1234, BA 405, AS 34.
                        A flight id is an integer eg.1234.
                        Do NOT use this tool if you have a flight number.
                        Do NOT guess an airline or flight number.
                        """,
            args_schema=FlightIdInput,
        ),
        StructuredTool.from_function(
            coroutine=search_flights_by_number,
            name="Search Flights By Flight Number",
            description="""
                        Use this tool to get info for a specific flight. Do NOT use this tool with a flight id.
                        Takes an airline and flight number and returns info on the flight.
                        Do NOT guess an airline or flight number.
                        A flight number is a code for an airline service consisting of two-character
                        airline designator and a 1 to 4 digit number ex. OO123, DL 1234, BA 405, AS 3452.
                        If the tool returns more than one option choose the date closes to today.
                        """,
            args_schema=FlightNumberInput,
        ),
        StructuredTool.from_function(
            coroutine=list_flights,
            name="List Flights",
            description="""
                        Use this tool to list all flights matching search criteria.
                        Takes an arrival airport, a departure airport, or both, filters by date and returns all matching flights.
                        The agent can decide to return the results directly to the user.
                        Input of this tool must be in JSON format and include all three inputs - arrival_airport, departure_airport, and date.
                        Example:
                        {{
                            "departure_airport": "SFO",
                            "arrival_airport": null,
                            "date": null
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
            coroutine=get_amenity,
            name="Get Amenity",
            description="""
                        Use this tool to get info for a specific airport amenity.
                        Takes an id and returns info on the amenity.
                        Do NOT guess an amenity id. Use Search Amenities to search by name.
                        Always use the id from the search_amenities tool.
                        """,
            args_schema=AmenityIdInput,
        ),
        StructuredTool.from_function(
            coroutine=search_amenities,
            name="Search Amenities",
            description="""
                        Use this tool to search amenities by name or to recommended airport amenities at SFO.
                        If user provides flight info, use 'Get Flight' and 'Get Flights by Number'
                        first to get gate info and location.
                        Only recommend amenities that are returned by this query.
                        Find amenities close to the user by matching the terminal and then comparing
                        the gate numbers. Gate number iterate by letter and number, example A1 A2 A3
                        B1 B2 B3 C1 C2 C3. Gate A3 is close to A2 and B1.
                        """,
            args_schema=QueryInput,
        ),
    ]


# Tools for agent
tools = initialize_tools()
