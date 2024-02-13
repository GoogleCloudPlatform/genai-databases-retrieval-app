# Copyright 2024 Google LLC
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

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar

import aiohttp

# aiohttp context
connector = None


class classproperty:
    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)


class Orchestration(ABC):
    client: aiohttp.ClientSession

    @classproperty
    @abstractmethod
    def kind(cls):
        pass

    @classmethod
    @abstractmethod
    async def create(cls, history: List[Any]) -> "Orchestration":
        pass

    async def invoke(self, prompt: str):
        raise NotImplementedError("Subclass should implement this!")

    @staticmethod
    async def get_connector():
        global connector
        if connector is None:
            connector = aiohttp.TCPConnector(limit=100)
        return connector

    @staticmethod
    async def handle_error_response(response):
        if response.status != 200:
            return f"Error sending {response.method} request to {str(response.url)}): {await response.text()}"

    @staticmethod
    async def create_client_session() -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            connector=await Orchestration.get_connector(),
            connector_owner=False,
            headers={},
            raise_for_status=True,
        )

    def close(self):
        raise NotImplementedError("Subclass should implement this!")


ais: Dict[str, Orchestration] = {}


async def create(orchestration: str, history: List[Any]) -> Orchestration:
    for cls in Orchestration.__subclasses__():
        s = f"{orchestration} == {cls.kind}"
        if orchestration == cls.kind:
            return await cls.create(history)  # type: ignore
    raise TypeError(f"No orchestration of kind {orchestration}")
    return
