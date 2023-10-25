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


from typing import Optional

from fastapi import APIRouter, Request
from langchain.embeddings.base import Embeddings

import datastore

routes = APIRouter()


@routes.get("/")
async def root():
    return {"message": "Hello World"}


@routes.get("/airports")
async def get_airport(id: int, request: Request):
    ds: datastore.Client = request.app.state.datastore
    results = await ds.get_airport(id)
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

    results = await ds.amenities_search(query_embedding, 0.3, top_k)
    return results


@routes.get("/flights")
async def get_flight(id: int, request: Request):
    ds: datastore.Client = request.app.state.datastore
    flights = await ds.get_flight(id)
    return flights


@routes.get("/flights/search")
async def search_flights(
    request: Request,
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
):
    ds: datastore.Client = request.app.state.datastore
    flights = await ds.search_flights(departure_airport, arrival_airport)
    return flights
