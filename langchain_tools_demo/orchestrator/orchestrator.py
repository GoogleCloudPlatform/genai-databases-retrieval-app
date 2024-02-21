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
from abc import ABC, abstractmethod
from typing import Any


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

    @abstractmethod
    def user_session_exist(self, uuid: str) -> bool:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def user_session_create(self, session: dict[str, Any]):
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def user_session_invoke(self, uuid: str, prompt: str) -> str:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    def user_session_reset(self, uuid: str):
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    def get_user_session(self, uuid: str) -> Any:
        raise NotImplementedError("Subclass should implement this!")

    def set_user_session_header(self, uuid: str, user_id_token: str):
        user_session = self.get_user_session(uuid)
        user_session.client.headers["User-Id-Token"] = f"Bearer {user_id_token}"


def createOrchestrator(orchestrator: str) -> "BaseOrchestrator":
    for cls in BaseOrchestrator.__subclasses__():
        s = f"{orchestrator} == {cls.kind}"
        print(s)
        if orchestrator == cls.kind:
            return cls()  # type: ignore
    raise TypeError(f"No orchestration of kind {orchestrator}")
