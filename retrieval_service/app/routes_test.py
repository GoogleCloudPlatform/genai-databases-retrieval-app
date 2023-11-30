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

from ipaddress import IPv4Address
import requests
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pytest

import models
import datetime
from datastore.providers import postgres

from . import init_app
from .app import AppConfig
from .helpers import get_env_var

GOOGLE_CLIENT_ID = (
    "64747076245-i1o9a69imntsgqaust9c9igd77r4creh.apps.googleusercontent.com"
)
DB_USER = "postgres"
DB_PASS = "postgres"
DB_NAME = "assistantdemo"
DB_HOST = "127.0.0.1"


@pytest.fixture(scope="module")
def app():
    cfg = AppConfig(
        datastore=postgres.Config(
            kind="postgres",
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            host=IPv4Address(DB_HOST),
        )
    )
    app = init_app(cfg)
    if app is None:
        raise TypeError("app did not initialize")
    return app


def test_hello_world(app):
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}


def test_naive(app):
    with TestClient(app) as client:
        response = client.get(
            "/flights",
            params={"flight_id": 1935},
        )
    assert response.status_code == 200
    output = response.json()
    assert output
    assert models.Flight.model_validate(output)


def test_get_flight(app):
    access_token = "ya29.a0AfB_byCi13amQxK-BXJlFv0xSmIwjb8SCuNmT04P9LZC16pOQzK1lXuIVxrbCzrGe87NnXRJG7TMZFeXTk4krLc-chzkHjJ4jr4v2B54lA2j47BufOPscWmZxUSyrBJFW-SHOwzhhtUmFjPvX39a8VtCYtsRctDD2o-6aCgYKAewSARISFQHGX2MiBPvHAJzIsNNW_8Ev-fFb5A0171"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    with TestClient(app) as client:
        response = client.get(
            "/flights",
            headers=headers,
            params={"flight_id": 1935},
        )
    print("--------------------------------------------------------")
    print(response)
    print("--------------------------------------------------------")

    # assert response.status_code == 200
    # output = response.json()
    # assert output
    # assert models.Flight.model_validate(output)


# def test_authorized_endpoint(app):
#     access_token = "ya29.a0AfB_byCi13amQxK-BXJlFv0xSmIwjb8SCuNmT04P9LZC16pOQzK1lXuIVxrbCzrGe87NnXRJG7TMZFeXTk4krLc-chzkHjJ4jr4v2B54lA2j47BufOPscWmZxUSyrBJFW-SHOwzhhtUmFjPvX39a8VtCYtsRctDD2o-6aCgYKAewSARISFQHGX2MiBPvHAJzIsNNW_8Ev-fFb5A0171"
#     params = {
#         "airline": "ANA",
#         "flight_number": "999",
#         "departure_airport": "SFO",
#         "arrival_airport": "NYC",
#         "departure_time": datetime.datetime(2023, 12, 25, 10, 30, 0),
#         "arrival_time": datetime.datetime(2023, 12, 25, 16, 30, 0),
#     }
#     with TestClient(app) as client:
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json",
#         }

#         response = client.post("/ticket", headers=headers, params=params)

#     assert response.status_code == 200


# def test_unauthorized_endpoint(base_url, invalid_access_token):
#     url = f"{base_url}/your-unauthorized-endpoint"
#     headers = {"Authorization": f"Bearer {invalid_access_token}"}

#     response = requests.get(url, headers=headers)

#     # Assert that the response status code is as expected
#     assert response.status_code == 401
