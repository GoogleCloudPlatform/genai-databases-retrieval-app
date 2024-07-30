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

from pydantic import BaseModel
from neo4j import GraphDatabase

from typing import Literal

from .. import datastore

NEO4J_IDENTIFIER = "neo4j"

class Config(BaseModel):
    kind: Literal["neo4j"]
    uri: str
    user: str
    password: str

class Client(datastore.Client[Config]):
    __driver: GraphDatabase.driver

    @datastore.classproperty
    def kind(cls):
        return NEO4J_IDENTIFIER

    def __init__(self, driver):
        self.__driver = driver

    @classmethod
    async def create(cls, config: Config) -> "Client":
        return cls(GraphDatabase.driver(config.uri, auth=(config.user, config.password)))
    
    async def close(self):
        self.__driver.close()

    


