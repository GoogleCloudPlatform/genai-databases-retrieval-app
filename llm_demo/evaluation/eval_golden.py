# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

goldens = [
    {
        "Search Airport Tool": [
            {
                "query": "What is the airport located in San Francisco?",
                "tool_calls": [
                    {
                        "name": "Search Airport",
                        "arguments": {"city": "San Francisco"},
                    },
                ],
            },
            {
                "query": "Tell me more about Denver International Airport?",
                "tool_calls": [
                    {
                        "name": "Search Airport",
                        "arguments": {
                            "city": "Denver",
                            "name": "Denver International Airport",
                        },
                    },
                ],
            },
        ]
    },
    {
        "Search Flights By Flight Number Tool": [
            {
                "query": "What is the departure gate for flight CY 922?",
                "tool_calls": [
                    {
                        "name": "Search Flights By Flight Number",
                        "arguments": {
                            "airline": "CY",
                            "flight_number": "922",
                        },
                    },
                ],
            },
            {
                "query": "What is flight CY 888 flying to?",
                "tool_calls": [
                    {
                        "name": "Search Flights By Flight Number",
                        "arguments": {
                            "airline": "CY",
                            "flight_number": "888",
                        },
                    },
                ],
            },
        ]
    },
    {
        "List Flights Tool": [
            {
                "query": "What flights are headed to JFK tomorrow?",
                "tool_calls": [
                    {
                        "name": "List Flights",
                        "arguments": {
                            "arrival_airport": "JFK",
                            "date": "2023-01-02",
                        },
                    },
                ],
            },
            {
                "query": "Is there any flight from SFO to DEN?",
                "output": "I will need the date to retrieve relevant flights.",
            },
        ]
    },
    {
        "Search Amenities Tool": [
            {
                "query": "Are there any luxury shops?",
                "tool_calls": [
                    {
                        "name": "Search Amenities",
                        "arguments": {
                            "query": "luxury shops",
                        },
                    },
                ],
            },
            {
                "query": "Where can I get coffee near gate A6?",
                "tool_calls": [
                    {
                        "name": "Search Amenities",
                        "arguments": {
                            "query": "coffee near gate A6",
                        },
                    },
                ],
            },
        ]
    },
    {
        "Search Policies Tool": [
            {
                "query": "When can I cancel my flight?",
                "tool_calls": [
                    {
                        "name": "Search Policies",
                        "arguments": {
                            "query": "cancel flight",
                        },
                    },
                ],
            },
            {
                "query": "How many checked bags can I bring?",
                "tool_calls": [
                    {
                        "name": "Search Policies",
                        "arguments": {
                            "query": "checked bags",
                        },
                    },
                ],
            },
        ]
    },
    {
        "Insert Ticket": [
            {
                "query": "I would like to book flight CY 888 departing from SFO on 2024-01-01 at 6am.",
                "tool_calls": [
                    {
                        "name": "Insert Ticket",
                        "arguments": {
                            "airline": "CY",
                            "flight_number": "888",
                            "departure_airport": "SFO",
                            "departure_time": "2024-01-01 06:00:00",
                        },
                    },
                ],
            },
            {
                "query": "What flights are headed from SFO to DEN today?",
                "tool_calls": [
                    {
                        "name": "List Flights",
                        "arguments": {
                            "departure_airport": "SFO",
                            "arrival_airport": "DEN",
                            "date": "2024-01-01",
                        },
                    },
                ],
                "reset": False,
            },
            {
                "query": "I would like to book the first flight.",
                "tool_calls": [
                    {
                        "name": "Insert Ticket",
                        "arguments": {
                            "airline": "CY",
                            "flight_number": "888",
                            "departure_airport": "SFO",
                            "arrival_airport": "DEN",
                            "departure_time": "2024-01-01 05:00:00",
                            "arrival_time": "2024-01-01 08:00:00",
                        },
                    },
                ],
            },
        ]
    },
    {
        "List Tickets": [
            {
                "query": "Do I have any tickets?",
                "tool_calls": [
                    {
                        "name": "List Tickets",
                    },
                ],
            },
            {
                "query": "When is my next flight?",
                "tool_calls": [
                    {
                        "name": "List Tickets",
                    },
                ],
            },
        ]
    },
    {
        "Airline Related Question": [
            {
                "query": "What is Cymbal Air?",
                "output": "Cymbal Air is a passenger airline offering convenient flights to many cities around the world from its hub in San Francisco.",
            },
            {
                "query": "Where is the hub of cymbal air?",
                "output": "The hub of Cymbal Air is in San Francisco.",
            },
        ]
    },
    {
        "Assistant Related Question": [
            {
                "query": "What can you help me with?",
                "output": "I can help to book flights and answer a wide range of questions pertaining to travel on Cymbal Air, as well as amenities of San Francisco Airport.",
            },
            {
                "query": "Can you help me book tickets?",
                "output": "Yes, I can help with several tools such as search airports, list tickets, book tickets.",
            },
        ]
    },
    {
        "Out-Of-Context Question": [
            {
                "query": "Can you help me solve math problems?",
                "output": "Sorry, I am not given the tools for this.",
            },
            {
                "query": "Who is the CEO of Google?",
                "output": "Sorry, I am not given the tools for this.",
            },
        ]
    },
    {
        "Multitool Selections": [
            {
                "query": "Where can I get a snack near the gate for flight CY 352?",
                "tool_calls": [
                    {
                        "name": "Search Flights By Flight Number",
                        "arguments": {
                            "airline": "CY",
                            "flight_number": "352",
                        },
                    },
                    {
                        "name": "Search Amenities",
                        "arguments": {
                            "query": "snack near gate A2.",
                        },
                    },
                ],
            },
            {
                "query": "What are some flights from SFO to Chicago tomorrow?",
                "tool_calls": [
                    {
                        "name": "Search Airport",
                        "arguments": {
                            "city": "Chicago",
                        },
                    },
                    {
                        "name": "List Flights",
                        "arguments": {
                            "departure_airport": "SFO",
                            "arrival_airport": "ORD",
                            "date": "2024-01-02",
                        },
                    },
                ],
            },
        ]
    },
]
