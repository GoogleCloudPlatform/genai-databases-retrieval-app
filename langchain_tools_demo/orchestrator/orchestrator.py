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

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from aiohttp import ClientSession, TCPConnector

BASE_HISTORY = [
    {
        "type": "ai",
        "data": {"content": "I am an SFO Airport Assistant, ready to assist you."},
    }
]


class classproperty:
    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)


class BaseOrchestrator(ABC):
    @classproperty
    @abstractmethod
    def kind(cls):
        pass

    @classmethod
    def create(cls, orchestrator: str) -> "BaseOrchestrator":
        for cls in BaseOrchestrator.__subclasses__():
            s = f"{orchestrator} == {cls.kind}"
            if orchestrator == cls.kind:
                return cls()
        raise TypeError(f"No orchestration of kind {orchestrator}")

    @abstractmethod
    async def create_ai(self, base_history: list[Any]):
        """Create and load an executor"""
        raise NotImplementedError("Subclass should implement this!")

    async def get_connector(self) -> TCPConnector:
        if self.connector is None:
            self.connector = TCPConnector(limit=100)
        return self.connector

    async def create_client_session(self) -> ClientSession:
        return ClientSession(
            connector=await self.get_connector(),
            connector_owner=False,
            headers={},
            raise_for_status=True,
        )

    async def get_agent(self, session: dict[str, Any], user_id_token: Optional[str]):
        if "uuid" not in session:
            session["uuid"] = str(uuid.uuid4())
        id = session["uuid"]
        if "history" not in session:
            session["history"] = BASE_HISTORY
        if id not in self.ais:
            self.ais[id] = await self.create_ai(session["history"])
        ai = self.ais[id]
        if user_id_token is not None:
            ai.client.headers["User-Id-Token"] = f"Bearer {user_id_token}"
        return ai

    def close_clients(self):
        close_client_tasks = [asyncio.create_task(a.close()) for a in self.ais.values()]
        asyncio.gather(*close_client_tasks)

    async def close_client(self, uuid: str):
        await self.ais[uuid].client.close()

    def remove_ai(self, uuid: str):
        del self.ais[uuid]
