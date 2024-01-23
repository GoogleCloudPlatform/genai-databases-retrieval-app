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

import aiohttp
import google.auth.transport.requests  # type: ignore
import google.oauth2.id_token  # type: ignore
from langchain.tools import StructuredTool, tool
from pydantic.v1 import BaseModel, Field

BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
CLOUD_RUN_CREDENTIALS = None


def filter_none_values(params: dict) -> dict:
    return {key: value for key, value in params.items() if value is not None}


def get_id_token():
    global CLOUD_RUN_CREDENTIALS

    if os.getenv("K_SERVICE"):
        auth_req = google.auth.transport.requests.Request()

        if CLOUD_RUN_CREDENTIALS is None:
            CLOUD_RUN_CREDENTIALS = google.oauth2.id_token.fetch_id_token_credentials(
                BASE_URL, auth_req
            )

        if not CLOUD_RUN_CREDENTIALS.valid:
            CLOUD_RUN_CREDENTIALS.refresh(auth_req)
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

    return CLOUD_RUN_CREDENTIALS.token


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
    date: Optional[str] = Field(description="Date of flight departure")


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
        """
        Use this tool to search amenities by name or to recommended airport amenities at SFO.
        If user provides flight info, use 'Get Flight' and 'Get Flights by Number'
        first to get gate info and location.
        Only recommend amenities that are returned by this query.
        Find amenities close to the user by matching the terminal and then comparing
        the gate numbers. Gate number iterate by letter and number, example A1 A2 A3
        B1 B2 B3 C1 C2 C3. Gate A3 is close to A2 and B1.
        """
        response = await client.get(
            url=f"{BASE_URL}/amenities/search",
            params={"top_k": "5", "query": query},
            headers=get_headers(client),
        )

        response = await response.json()
        return response

    return search_amenities


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
            coroutine=generate_list_flights(client),
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
            coroutine=generate_search_amenities(client),
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
