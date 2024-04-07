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

import os
from typing import Any, Mapping, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from google.auth.transport import requests  # type:ignore
from google.oauth2 import id_token  # type:ignore
from langchain_core.embeddings import Embeddings

import datastore
from helpers import UIFriendlyLogger

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


def build_result(results, ufl: UIFriendlyLogger | None = None):
    result = {"result": results}
    if ufl is not None and ufl.get_log() != "":
        result["trace"] = ufl.get_log()
    return result


async def get_user_info(request):
    headers = request.headers
    token = _ParseUserIdToken(headers)
    try:
        id_info = id_token.verify_oauth2_token(
            token, requests.Request(), audience=request.app.state.client_id
        )

        return {
            "user_id": id_info["sub"],
            "user_name": id_info["name"],
            "user_email": id_info["email"],
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
    return build_result(results)


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
    return build_result(results)


@routes.get("/amenities")
async def get_amenity(id: int, request: Request):
    ds: datastore.Client = request.app.state.datastore
    results = await ds.get_amenity(id)
    return build_result(results)


@routes.get("/amenities/search")
async def amenities_search(
    request: Request,
    query: str,
    top_k: int,
    open_time: Optional[str] = None,
    open_day: Optional[str] = None,
):
    ufl = UIFriendlyLogger()
    ufl.log_section_header("Attempting to use vector / embedding search for amenities")
    ds: datastore.Client = request.app.state.datastore
    days_of_week = [
        "sunday",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
    ]
    if open_day and open_day not in days_of_week:
        raise HTTPException(
            status_code=422,
            detail="open_day value not valid",
        )

    if (open_time and not open_day) or (open_day and not open_time):
        raise HTTPException(
            status_code=422,
            detail="Request requires query params: provide none or both of open_time and open_day",
        )

    embed_service: Embeddings = request.app.state.embed_service
    query_embedding = embed_service.embed_query(query)

    results = await ds.amenities_search(
        query, query_embedding, 0.5, top_k, ufl, open_time, open_day
    )
    return build_result(results, ufl)


@routes.get("/flights")
async def get_flight(flight_id: int, request: Request):
    ds: datastore.Client = request.app.state.datastore
    flights = await ds.get_flight(flight_id)
    return build_result(flights)


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
    return build_result(flights)


@routes.get("/seats/search")
async def search_seats(
    request: Request,
    airline: str,
    flight_number: str,
    departure_airport: str,
    departure_time: str,
    seat_row: Optional[int] = None,
    seat_letter: Optional[str] = None,
    seat_class: Optional[str] = None,
    seat_type: Optional[str] = None,
):
    ds: datastore.Client = request.app.state.datastore
    seats = await ds.search_flight_seats(
        airline,
        flight_number,
        departure_airport,
        departure_time,
        seat_row,
        seat_letter,
        seat_class,
        seat_type,
    )
    return build_result(seats)


@routes.get("/seats/validate")
async def validate_seat(
    request: Request,
    airline: str,
    flight_number: str,
    departure_airport: str,
    departure_time: str,
    seat_row: int,
    seat_letter: str,
):
    ufl = UIFriendlyLogger()
    ufl.log_section_header("Validating that seat is available on flight")
    ds: datastore.Client = request.app.state.datastore
    result = await ds.validate_seat(
        airline,
        flight_number,
        departure_airport,
        departure_time,
        seat_row,
        seat_letter,
        ufl,
    )
    return build_result(result, ufl)


@routes.get("/tickets/validate")
async def validate_ticket(
    request: Request,
    airline: str,
    flight_number: str,
    departure_airport: str,
    departure_time: str,
):
    ufl = UIFriendlyLogger()
    ufl.log_section_header("Validating that flight is available")
    ds: datastore.Client = request.app.state.datastore
    result = await ds.validate_ticket(
        airline, flight_number, departure_airport, departure_time, ufl
    )
    return build_result(result, ufl)


@routes.post("/tickets/insert")
async def insert_ticket(
    request: Request,
    airline: str,
    flight_number: str,
    departure_airport: str,
    arrival_airport: str,
    departure_time: str,
    arrival_time: str,
    seat_row: Optional[int] = None,
    seat_letter: Optional[str] = None,
):
    ufl = UIFriendlyLogger()
    ufl.log_section_header(
        "Attempting to insert the requested ticket into the database"
    )
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
        ufl,
        seat_row,
        seat_letter,
    )
    return build_result(result, ufl)


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
    return build_result(results)


@routes.get("/policies/search")
async def policies_search(query: str, top_k: int, request: Request):
    ufl = UIFriendlyLogger()
    ufl.log_section_header("Attempting to use vector / embedding search for policies")
    ds: datastore.Client = request.app.state.datastore

    embed_service: Embeddings = request.app.state.embed_service
    query_embedding = embed_service.embed_query(query)

    results = await ds.policies_search(query, query_embedding, 0.5, top_k, ufl)
    return build_result(results, ufl)
