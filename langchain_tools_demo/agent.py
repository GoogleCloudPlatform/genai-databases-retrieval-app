import os
from langchain.agents import AgentType, initialize_agent
from langchain.llms import VertexAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool, StructuredTool
import google.auth.transport.requests
import google.oauth2.id_token
from pydantic.v1 import BaseModel, Field
from langchain.agents.mrkl.base import ZeroShotAgent
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
import requests

DEBUG = bool(os.getenv("DEBUG", default=False))
BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")


def init_agent(history):
    """Load an agent executor with tools and LLM"""
    print("Initializing agent..")
    llm = VertexAI(max_output_tokens=512, verbose=DEBUG)

    # Add Chat history
    # chat_history = ChatMessageHistory()
    # for message in history:
    #     if message["role"] == "assistant":
    #         chat_history.add_ai_message(message["content"])
    #     else:
    #         chat_history.add_user_message(message["content"])
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        # return_messages=True,
        # ai_prefix="assistant",
        # chat_history=chat_history,
    )
    # memory.chat_memory.add_ai_message("whats up?")
    # memory.save_context(history)
    # memory.load_memory_variables({})
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

    # results = (
    #     [
    #         """Here are is list of toys related to the query in JSON format. Only
    #         use this list in making recommendations to the customer."""
    #     ]
    #     + [f"{r}" for r in response.json()]
    # )
    # if len(results) <= 1:
    #     return """There are no toys matching that query. Please try again or
    #             let the user know there are no results."""
    # output = "\n".join(results)
    # return output


def get_id_token():
    auth_req = google.auth.transport.requests.Request()
    target_audience = BASE_URL

    return google.oauth2.id_token.fetch_id_token(auth_req, target_audience)


def get_flight(id: int):
    # response = requests.get(
    #     f"{BASE_URL}/flight/{id}",
    #     headers={"Authorization": f"Bearer {get_id_token()}"},
    # )

    # if response.status_code != 200:
    #     return f"Error trying to find flight: {response.text}"

    # return response.json()

    return {
        "id": id,
        "departure_time": "11am",
        "departure_airport": "SFO",
        "depatrue_gate": "A13",
        "arrival_gate": "N2",
        "arrival_time": "1pm",
        "arrival_airport": "SEA",
        "boarding_time": "10:45am",
        "airline": "Alaska Airlines",
    }


def list_flights(departure_airport: str, arrival_airport: str, date: str):
    # params = {"top_k": "5", "query": desc}

    # response = requests.get(
    #     f"{BASE_URL}/flight/search",
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
    # response = requests.get(
    #     f"{BASE_URL}/amenities/{id}",
    #     headers={"Authorization": f"Bearer {get_id_token()}"},
    # )

    # if response.status_code != 200:
    #     return f"Error trying to find flight: {response.text}"

    # return response.json()
    return {
        "id": id,
        "name": "Hudson Bay",
        "description": "Get your airport snalcs",
        "location": "Near Gate A13",
        "terminal": "Terminal 3",
        "category": "shop",
        "hours": "Sunday-Saturday 7:00 am-11:00 pm",
        "content": "This amenity is a <category>. <description>",
    }


def search_amenities(query: str):
    # params = {"top_k": "5", "query": desc}

    # response = requests.get(
    #     f"{BASE_URL}/amenities/search",
    #     params,
    #     headers={"Authorization": f"Bearer {get_id_token()}"},
    # )
    # if response.status_code != 200:
    #     return f"Error trying to find flight: {response.text}"

    # return response.json()
    return [
        {
            "id": 1,
            "name": "Hudson Bay",
            "description": "Get your airport snacks",
            "location": "Near Gate A13",
            "terminal": "Terminal 3",
            "category": "shop",
            "hours": "Sunday-Saturday 7:00 am-11:00 pm",
            "content": "This amenity is a <category>. <description>",
        },
        {
            "id": 2,
            "name": "Beechers",
            "description": "Get your airport snacks",
            "location": "Near Gate B3",
            "terminal": "Terminal 3",
            "category": "restaurant",
            "hours": "Sunday-Saturday 7:00 am-11:00 pm",
            "content": "This amenity is a <category>. <description>",
        },
    ]


def get_airport(id: int):
    # response = requests.get(
    #     f"{BASE_URL}/airport/{id}",
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
    #     f"{BASE_URL}/airport/semantic_lookup",
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
    id: int = Field()


class QueryInput(BaseModel):
    query: str = Field()  # TODO: add top k?


class ListFlights(BaseModel):
    departure_airport: str = Field()
    arrival_airport: str = Field()
    date: str = Field()  # TODO: check this field type


tools = [
    Tool.from_function(
        name="get_flight",  # Name must be unique
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
        description="Use this tool to find recommended airport amenities. Returns several amenities that are related to the query. Only recommend amenities that are returned by this query.",
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
