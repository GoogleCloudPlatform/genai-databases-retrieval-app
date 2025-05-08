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

from contextlib import asynccontextmanager
from ipaddress import IPv4Address, IPv6Address
from typing import Optional

import os
from fastapi import FastAPI
from langchain_google_vertexai import VertexAIEmbeddings
from pydantic import BaseModel

import datastore

from .routes import routes

EMBEDDING_MODEL_NAME = "text-embedding-005"


class AppConfig(BaseModel):
    host: IPv4Address | IPv6Address = IPv4Address("127.0.0.1")
    port: int = 8080
    datastore: datastore.Config
    clientId: Optional[str] = None


def parse_config(path: str) -> AppConfig:
    config = {}

    # Base config
    base_config_vars = {
        "HOST": "host",
        "PORT": "port",
        "CLIENT_ID": "clientId",
    }

    for envVar, configVar in base_config_vars.items():
        if os.environ.get(envVar):
            config[configVar] = os.environ.get(envVar)
    
    # Datastore config
    datastore_config = {}
    datastore_config_vars = ["kind", "host", "port", "project", "region", "cluster", "instance", "database", "user", "password"]

    for configVar in datastore_config_vars:
        envVar = "DATASTORE_" + configVar.upper()

        if os.environ.get(envVar):
            datastore_config[configVar] = os.environ.get(envVar)

    if len(datastore_config) > 0:
        config["datastore"] = datastore_config

    return AppConfig(**config)


# gen_init is a wrapper to initialize the datastore during app startup
def gen_init(cfg: AppConfig):
    async def initialize_datastore(app: FastAPI):
        app.state.datastore = await datastore.create(cfg.datastore)
        app.state.embed_service = VertexAIEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        yield
        await app.state.datastore.close()

    return asynccontextmanager(initialize_datastore)


def init_app(cfg: AppConfig) -> FastAPI:
    app = FastAPI(lifespan=gen_init(cfg))
    app.state.client_id = cfg.clientId
    app.include_router(routes)
    return app
