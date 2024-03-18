# Copyright 2024 Google LLC
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

import aiohttp
from vertexai.preview import generative_models  # type: ignore

BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
CREDENTIALS = None

search_airports_func = generative_models.FunctionDeclaration(
    name="airports_search",
    description="""
                Use this tool to list all airports matching search criteria.
                Takes at least one of country, city, name, or all and returns all matching airports.
                This function could also be used to serach for airport information such as iata code.
                """,
    parameters={
        "type": "object",
        "properties": {
            "country": {"type": "string", "description": "country"},
            "city": {"type": "string", "description": "city"},
            "name": {
                "type": "string",
                "description": "Full or partial name of an airport",
            },
        },
    },
)

search_amenities_func = generative_models.FunctionDeclaration(
    name="amenities_search",
    description="""
                Use this tool to search amenities by name or to recommended airport amenities at SFO.
                If user provides flight info, use 'search_flights_by_number'
                first to get gate info and location.
                Only recommend amenities that are returned by this query.
                Find amenities close to the user by matching the terminal and then comparing
                the gate numbers. Gate number iterate by letter and number, example A1 A2 A3
                B1 B2 B3 C1 C2 C3. Gate A3 is close to A2 and B1.
                top_k value is defaulted to 5.
                """,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "top_k": {
                "type": "integer",
                "description": "Number of matching amenities to return. Default this value to 5.",
            },
        },
        "required": ["query", "top_k"],
    },
)

search_policies_func = generative_models.FunctionDeclaration(
    name="policies_search",
    description="Use this tool to search for cymbal air passenger policy. Policy that are listed is unchangeable. You will not answer any questions outside of the policy given. Policy includes information on ticket purchase and changes, baggage, check-in and boarding, special assistance, overbooking, flight delays and cancellations. If top_k is not specified, default to 5.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "top_k": {
                "type": "integer",
                "description": "Number of matching policy to return. Default this value to 5.",
            },
        },
    },
)

search_flights_by_number_func = generative_models.FunctionDeclaration(
    name="search_flights_by_number",
    description="""
                Use this tool to get info for a specific flight. Do NOT use this tool with a flight id.
                Takes an airline and flight number and returns info on the flight.
                Do NOT guess an airline or flight number.
                A flight number is a code for an airline service consisting of two-character
                airline designator and a 1 to 4 digit number ex. OO123, DL 1234, BA 405, AS 3452.
                If the tool returns more than one option choose the date closes to today.
                """,
    parameters={
        "type": "object",
        "properties": {
            "airline": {
                "type": "string",
                "description": "A code for an airline service consisting of two-character airline designator.",
            },
            "flight_number": {
                "type": "string",
                "description": "A 1 to 4 digit number of the flight.",
            },
        },
        "required": ["airline", "flight_number"],
    },
)

list_flights_func = generative_models.FunctionDeclaration(
    name="list_flights",
    description="""
                Use this tool to list all flights matching search criteria.
                Takes an arrival airport, a departure airport, or both, filters by date and returns all matching flights.
                Date must be provided, prompt user if it is not given.
                The format of date must be YYYY-MM-DD. Convert terms like 'today' or 'yesterday' to a valid date format.
                If iata code is not provided for departure_airport or arrival_airport, use airports_search function to get iata code.
                """,
    parameters={
        "type": "object",
        "properties": {
            "departure_airport": {
                "type": "string",
                "description": "The iata code for flight departure airport. Example: 'SFO', 'DEN'.",
            },
            "arrival_airport": {
                "type": "string",
                "description": "The iata code for flight arrival airport. Example: 'SFO', 'DEN'.",
            },
            "date": {
                "type": "string",
                "description": "The date of flight must be in the following format: YYYY-MM-DD.",
            },
        },
        "required": ["date"],
    },
)

insert_ticket_func = generative_models.FunctionDeclaration(
    name="insert_ticket",
    description="Use this tool to book a flight ticket for the user.",
    parameters={
        "type": "object",
        "properties": {
            "airline": {
                "type": "string",
                "description": "A code for an airline service consisting of two-character airline designator.",
            },
            "flight_number": {
                "type": "string",
                "description": "A 1 to 4 digit number of the flight.",
            },
            "departure_airport": {
                "type": "string",
                "description": "The iata code for flight departure airport.",
            },
            "arrival_airport": {
                "type": "string",
                "description": "The iata code for flight arrival airport.",
            },
            "departure_time": {
                "type": "string",
                "description": "The departure time for flight.",
            },
            "arrival_time": {
                "type": "string",
                "description": "The arrival time for flight.",
            },
        },
        "required": [
            "airline",
            "flight_number",
            "departure_airport",
            "arrival_airport",
            "departure_time",
            "arrival_time",
        ],
    },
)

list_tickets_func = generative_models.FunctionDeclaration(
    name="list_tickets",
    description="Use this tool to list a user's flight tickets. This tool takes no input parameters and returns a list of current user's flight tickets.",
    parameters={
        "type": "object",
    },
)


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
    response = await response.json()
    return response


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


def function_request(function_call_name: str) -> str:
    functions_url = {
        "airports_search": "airports/search",
        "search_flights_by_number": "flights/search",
        "list_flights": "flights/search",
        "amenities_search": "amenities/search",
        "policies_search": "policies/search",
        "insert_ticket": "tickets/insert",
        "list_tickets": "tickets/list",
    }
    return functions_url[function_call_name]


def assistant_tool():
    return generative_models.Tool(
        function_declarations=[
            search_airports_func,
            search_amenities_func,
            search_policies_func,
            search_flights_by_number_func,
            list_flights_func,
            insert_ticket_func,
            list_tickets_func,
        ],
    )


def get_confirmation_needing_tools():
    return ["insert_ticket"]
