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


from typing import Annotated, Optional, Mapping, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from langchain.embeddings.base import Embeddings
from fastapi.security import OAuth2AuthorizationCodeBearer
import datastore
from google.auth.transport import requests
from google.oauth2 import id_token
from fastapi.security import OAuth2PasswordBearer

routes = APIRouter()

# GOOGLE_CLIENT_ID = (
#     "64747076245-i1o9a69imntsgqaust9c9igd77r4creh.apps.googleusercontent.com"
# )
GOOGLE_CLIENT_ID = (
    "548341735270-6qu1l8tttfuhmt7nbfb7a4q6j4hso2f7.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = 
GOOGLE_REDIRECT_URI = "http://localhost:8081/login/google"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# @routes.post("/login/google")
# async def login_google():
# return {
#     "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
# }


@routes.post("/auth/google")
async def auth_google(code: str):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    access_token = response.json().get("access_token")
    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return user_info.json()


@routes.get("/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, GOOGLE_CLIENT_SECRET, algorithms=["HS256"])





def _ParseBearerToken(headers: Mapping[str, Any]) -> Optional[str]:
    """Parses the bearer token out of the request headers."""
    # authorization_header = headers.lower()
    authorization_header = headers.get("authorization")
    print(authorization_header)
    if not authorization_header:
        print("no authorization header")
        return None

    parts = str(authorization_header).split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        return None

    return parts[1]


async def get_current_user(headers: Mapping[str, Any]):
    token = _ParseBearerToken(headers)
    print(token)
    try:
        id_info = _id_token_async.verify_oauth2_token(
            token, requests.Request(), audience=GOOGLE_CLIENT_ID
        )

        return {
            "user_id": id_info["sub"],
            "name": id_info["name"],
            "email": id_info["email"],
        }

    except Exception as e:  # pylint: disable=broad-except
        print(e)


@routes.get("/")
async def root(request: Request):
    user = request.session.get("user")
    if user is not None:
        return {id: user.id}
    return {"error": "Un-authorized"}


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
async def get_flight(
    flight_id: int,
    request: Request,
):
    user_info = await get_current_user(request.headers)
    print(user_info)
    if user_info is None:
        raise HTTPException(
            status_code=401,
            detail="User login required for data insertion",
        )
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


@routes.post("/ticket")
async def insert_ticket(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    airline: str,
    flight_number: str,
    departure_airport: str,
    arrival_airport: str,
    departure_time: str,
    arrival_time: str,
):
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="User login required for data insertion",
        )
    ds: datastore.Client = request.app.state.datastore
    results = await ds.insert_ticket(
        current_user.get("user_id"),
        current_user.get("user_name"),
        current_user.get("user_email"),
        airline,
        flight_number,
        departure_airport,
        arrival_airport,
        departure_time,
        arrival_time,
    )
    return results
