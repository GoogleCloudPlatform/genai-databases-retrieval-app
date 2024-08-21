# Copyright 2023 Google LLC
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

from typing import Any, Mapping, Optional

from fastapi import APIRouter, HTTPException, Request
from google.auth.transport import requests  # type:ignore
from google.oauth2 import id_token  # type:ignore
from langchain_core.embeddings import Embeddings

import datastore

routes = APIRouter()


def _ParseUserIdToken(headers: Mapping[str, Any]) -> Optional[str]:
    """Parses the bearer token out of the request headers."""
    # authorization_header = headers.lower()
    user_id_token_header = headers.get("User-Id-Token")
    if not user_id_token_header:
        raise Exception("no user authorization header")

    parts = str(user_id_token_header).split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        raise Exception("Invalid ID token")

    return parts[1]


async def get_user_info(request):
    headers = request.headers
    token = _ParseUserIdToken(headers)
    try:
        id_info = id_token.verify_oauth2_token(
            token, requests.Request(), audience=request.app.state.client_id
        )

        return {
            "user_id": id_info.get("sub"),
            "user_name": id_info.get("name"),
            "user_email": id_info.get("email"),
        }

    except Exception as e:  # pylint: disable=broad-except
        print(e)


@routes.get("/")
async def root():
    return {"message": "Hello World"}


@routes.get("/airports")
async def get_airport(
    request: Request,
    id: Optional[int] = None,
    iata: Optional[str] = None,
):
    ds: datastore.Client = request.app.state.datastore
    if id:
        results = await ds.get_airport_by_id(id)
    elif iata:
        results = await ds.get_airport_by_iata(iata)
    else:
        raise HTTPException(
            status_code=422,
            detail="Request requires query params: airport id or iata",
        )
    return results


@routes.get("/airports/search")
async def search_airports(
    request: Request,
    country: Optional[str] = None,
    city: Optional[str] = None,
    name: Optional[str] = None,
):
    if country is None and city is None and name is None:
        raise HTTPException(
            status_code=422,
            detail="Request requires at least one query params: country, city, or airport name",
        )

    ds: datastore.Client = request.app.state.datastore
    results = await ds.search_airports(country, city, name)
    return results


@routes.get("/amenities")
async def get_amenity(id: int, request: Request):
    ds: datastore.Client = request.app.state.datastore
    results = await ds.get_amenity(id)
    return results


@routes.get("/amenities/search")
async def amenities_search(query: str, top_k: int, request: Request):
    ds: datastore.Client = request.app.state.datastore

    embed_service: Embeddings = request.app.state.embed_service
    query_embedding = embed_service.embed_query(query)

    results = await ds.amenities_search(query_embedding, 0.5, top_k)
    return results


@routes.get("/flights")
async def get_flight(flight_id: int, request: Request):
    ds: datastore.Client = request.app.state.datastore
    flights = await ds.get_flight(flight_id)
    return flights


@routes.get("/flights/search")
async def search_flights(
    request: Request,
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    date: Optional[str] = None,
    airline: Optional[str] = None,
    flight_number: Optional[str] = None,
):
    ds: datastore.Client = request.app.state.datastore
    if date and (arrival_airport or departure_airport):
        flights = await ds.search_flights_by_airports(
            date, departure_airport, arrival_airport
        )
    elif airline and flight_number:
        flights = await ds.search_flights_by_number(airline, flight_number)
    else:
        raise HTTPException(
            status_code=422,
            detail="Request requires query params: arrival_airport, departure_airport, date, or both airline and flight_number",
        )
    return flights


@routes.post("/tickets/insert")
async def insert_ticket(
    request: Request,
    airline: str,
    flight_number: str,
    departure_airport: str,
    arrival_airport: str,
    departure_time: str,
    arrival_time: str,
):
    user_info = await get_user_info(request)
    if user_info is None:
        raise HTTPException(
            status_code=401,
            detail="User login required for data insertion",
        )
    ds: datastore.Client = request.app.state.datastore
    result = await ds.insert_ticket(
        user_info["user_id"],
        user_info["user_name"],
        user_info["user_email"],
        airline,
        flight_number,
        departure_airport,
        arrival_airport,
        departure_time,
        arrival_time,
    )
    return result


@routes.get("/tickets/validate")
async def validate_ticket(
    request: Request,
    airline: str,
    flight_number: str,
    departure_airport: str,
    departure_time: str,
):
    ds: datastore.Client = request.app.state.datastore
    result = await ds.validate_ticket(
        airline,
        flight_number,
        departure_airport,
        departure_time,
    )
    return result


@routes.get("/tickets/list")
async def list_tickets(
    request: Request,
):
    user_info = await get_user_info(request)
    if user_info is None:
        raise HTTPException(
            status_code=401,
            detail="User login required for data insertion",
        )
    ds: datastore.Client = request.app.state.datastore
    results = await ds.list_tickets(user_info["user_id"])
    return results


@routes.get("/policies/search")
async def policies_search(query: str, top_k: int, request: Request):
    ds: datastore.Client = request.app.state.datastore

    embed_service: Embeddings = request.app.state.embed_service
    query_embedding = embed_service.embed_query(query)

    results = await ds.policies_search(query_embedding, 0.5, top_k)
    return results
