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

import pytest

from fastapi import params
from fastapi.testclient import TestClient

from . import init_app
from .app import AppConfig
from .helpers import get_env_var
from extension_service.datastore.providers import postgres

DB_USER = get_env_var("DB_USER", "name of a postgres user")
DB_PASS = get_env_var("DB_PASS", "password for the postgres user")
DB_NAME = get_env_var("DB_NAME", "name of a postgres database")


@pytest.fixture(scope="module")
def app():
    cfg = AppConfig(
        datastore=postgres.Config(
            kind="postgres",
            user="my-user",
            password=":%M+}OH7uL(9V{lX",
            database="my_database",
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


def test_semantic_similiarity_search(app):
    with TestClient(app) as client:
        response = client.get(
            "/semantic_similarity_search",
            params={
                "query": "playing card games",
                "top_k": 5,
            },
        )
    assert response.status_code == 200
    output = response.json()
    assert len(output) == 5
    assert output[0]
