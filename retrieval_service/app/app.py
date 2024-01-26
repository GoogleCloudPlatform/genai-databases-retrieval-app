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
from contextlib import asynccontextmanager
from ipaddress import IPv4Address, IPv6Address

import yaml
from fastapi import FastAPI
from langchain.embeddings import VertexAIEmbeddings
from pydantic import BaseModel

import datastore

from .routes import routes

EMBEDDING_MODEL_NAME = "textembedding-gecko@001"


class AppConfig(BaseModel):
    host: IPv4Address | IPv6Address = IPv4Address("127.0.0.1")
    port: int = 8080
    datastore: datastore.Config
    clientId: str


def parse_config(path: str) -> AppConfig:
    with open(path, "r") as file:
        config = yaml.safe_load(file)
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
    os.environ["CLIENT_ID"] = cfg.clientId
    app = FastAPI(lifespan=gen_init(cfg))
    app.include_router(routes)
    return app
