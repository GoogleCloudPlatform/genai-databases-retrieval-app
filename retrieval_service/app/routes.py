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


from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from langchain.embeddings.base import Embeddings
from fastapi.security import OAuth2AuthorizationCodeBearer
import datastore
from google.auth.transport import requests
from google.oauth2 import _id_token_async

routes = APIRouter()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl="https://oauth2.googleapis.com/token"
)

GOOGLE_CLIENT_ID = (
    "548341735270-6qu1l8tttfuhmt7nbfb7a4q6j4hso2f7.apps.googleusercontent.com"
)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        id_info = _id_token_async.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )

        return {
            "user_id": id_info["sub"],
            "name": id_info["name"],
            "email": id_info["email"],
        }

    except Exception:  # pylint: disable=broad-except
        print("Error verifying oauth2 id_token")


@routes.get("/")
async def root():
    return {"message": "Hello World"}


@routes.get("/airports")
async def get_airport(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
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
