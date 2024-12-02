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
from datetime import date, datetime
from typing import Any, Dict, Optional

import aiohttp
import google.oauth2.id_token  # type: ignore
from google.auth import compute_engine  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from pydantic import BaseModel, Field
from toolbox_langchain_sdk import ToolboxClient  # type: ignore

BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:5000")
CREDENTIALS = None


def filter_none_values(params: Dict) -> Dict:
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

        response_json = await response.json()
        response_results = response_json.get("results")
        if len(response_results) < 1:
            return "There are no airports matching that query. Let the user know there are no results."
        else:
            return response_results

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

        response_json = await response.json()
        return response_json.get("results")

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

        response_json = await response.json()
        response_results = response_json.get("results")
        if len(response_results) < 1:
            return "There are no flights matching that query. Let the user know there are no results."
        else:
            return response_results

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

        response_json = await response.json()
        response_results = response_json.get("results")
        return response_results

    return search_amenities


def generate_search_policies(client: aiohttp.ClientSession):
    async def search_policies(query: str):
        response = await client.get(
            url=f"{BASE_URL}/policies/search",
            params={"top_k": "5", "query": query},
            headers=get_headers(client),
        )

        response_json = await response.json()
        response_results = response_json.get("results")
        return response_results

    return search_policies


class TicketInput(BaseModel):
    airline: str = Field(description="Airline unique 2 letter identifier")
    flight_number: str = Field(description="1 to 4 digit number")
    departure_airport: str = Field(
        description="Departure airport 3-letter code",
    )
    departure_time: datetime = Field(description="Flight departure datetime")
    arrival_airport: Optional[str] = Field(description="Arrival airport 3-letter code")
    arrival_time: Optional[datetime] = Field(description="Flight arrival datetime")


def generate_insert_ticket(client: aiohttp.ClientSession):
    async def insert_ticket(
        airline: str | None = None,
        flight_number: str | None = None,
        departure_airport: str | None = None,
        arrival_airport: str | None = None,
        departure_time: datetime | date | None = None,
        arrival_time: datetime | date | None = None,
    ):
        return f"Booking ticket on {airline} {flight_number}"

    return insert_ticket


async def insert_ticket(client: aiohttp.ClientSession, params: str):
    ticket_info = json.loads(params)
    response = await client.post(
        url=f"{BASE_URL}/tickets/insert",
        params={
            "airline": ticket_info.get("airline"),
            "flight_number": ticket_info.get("flight_number"),
            "departure_airport": ticket_info.get("departure_airport"),
            "arrival_airport": ticket_info.get("arrival_airport"),
            "departure_time": ticket_info.get("departure_time").replace("T", " "),
            "arrival_time": ticket_info.get("arrival_time").replace("T", " "),
        },
        headers=get_headers(client),
    )
    response_json = await response.json()
    return "Flight booking successful."


async def validate_ticket(client: aiohttp.ClientSession, ticket_info: Dict[Any, Any]):
    response = await client.get(
        url=f"{BASE_URL}/tickets/validate",
        params=filter_none_values(
            {
                "airline": ticket_info.get("airline"),
                "flight_number": ticket_info.get("flight_number"),
                "departure_airport": ticket_info.get("departure_airport"),
                "departure_time": ticket_info.get("departure_time", "").replace(
                    "T", " "
                ),
            }
        ),
        headers=get_headers(client),
    )
    response_json = await response.json()
    response_results = response_json.get("results")

    flight_info = {
        "airline": response_results.get("airline"),
        "flight_number": response_results.get("flight_number"),
        "departure_airport": response_results.get("departure_airport"),
        "arrival_airport": response_results.get("arrival_airport"),
        "departure_time": response_results.get("departure_time"),
        "arrival_time": response_results.get("arrival_time"),
    }
    return flight_info


def generate_list_tickets(client: aiohttp.ClientSession):
    async def list_tickets():
        response = await client.get(
            url=f"{BASE_URL}/tickets/list",
            headers=get_headers(client),
        )

        response_json = await response.json()
        tickets = response_json.get("results")
        if len(tickets) == 0:
            return {
                "results": "There are no upcoming tickets",
                "sql": response_json.get("sql"),
            }
        else:
            return response_json

    return list_tickets


# Tools for agent
async def initialize_tools(client: aiohttp.ClientSession):
    toolbox_client = ToolboxClient(
        BASE_URL,
        client,
    )
    # TODO: Remove the hardcoded bounded values with actual user data on successful login.
    toolbox_client.set_bounded_params(
        {
            "user_id": "12345678900",
            "user_name": "Someone",
            "user_email": "something@somewhere.com",
        }
    )
    return await toolbox_client.load_toolset()


def get_confirmation_needing_tools():
    return ["Insert Ticket"]
