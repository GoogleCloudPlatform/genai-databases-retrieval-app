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
from datastore.providers import postgres

from . import init_app
from .app import AppConfig
from .helpers import get_env_var

DB_USER = 
DB_PASS = 
DB_NAME = 
DB_HOST = 


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


ACCESS_TOKEN = "abc"
app = FastAPI()


def test_authorized_endpoint():
    with TestClient(app) as client:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        response = client.get(
            "/airports", headers=headers, params={"id": 1, "iata": "ABC"}
        )

        print(response)


# def test_unauthorized_endpoint(base_url, invalid_access_token):
#     url = f"{base_url}/your-unauthorized-endpoint"
#     headers = {"Authorization": f"Bearer {invalid_access_token}"}

#     response = requests.get(url, headers=headers)

#     # Assert that the response status code is as expected
#     assert response.status_code == 401
