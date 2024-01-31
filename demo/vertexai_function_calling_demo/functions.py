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

import os

from vertexai.preview import generative_models  # type: ignore

search_airports_func = generative_models.FunctionDeclaration(
    name="airports_search",
    description="Use this tool to list all airports matching search criteria. Takes at least one of country, city, name, or all of the above criteria. This function could also be used to search for airport information such as iata code.",
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
    description="Use this tool to search amenities by name or to recommend airport amenities at SFO. If top_k is not specified, default to 5",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "top_k": {
                "type": "integer",
                "description": "Number of matching amenities to return. Default this value to 5.",
            },
        },
    },
)

search_flights_by_number_func = generative_models.FunctionDeclaration(
    name="flights_search",
    description="Use this tool to get info for a specific flight. This function takes an airline and flight number and returns info on the flight.",
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
    },
)

list_flights_func = generative_models.FunctionDeclaration(
    name="flights_search",
    description="Use this tool to list all flights matching search criteria. This function takes an arrival airport, a departure airport, or both, filters by date and returns all matching flight. The format of date must be YYYY-MM-DD. Convert terms like today or yesterday to a valid date format.",
    parameters={
        "type": "object",
        "properties": {
            "departure_airport": {
                "type": "string",
                "description": "The iata code for flight departure airport.",
            },
            "arrival_airport": {
                "type": "string",
                "description": "The iata code for flight arrival airport.",
            },
            "date": {
                "type": "string",
                "description": "The date of flight must be in the following format: YYYY-MM-DD.",
            },
        },
    },
)


def assistant_tool():
    return generative_models.Tool(
        function_declarations=[
            search_airports_func,
            search_amenities_func,
            search_flights_by_number_func,
            list_flights_func,
        ],
    )
