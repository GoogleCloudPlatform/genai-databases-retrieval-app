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
from typing import Any, Optional


class classproperty:
    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)


class BaseOrchestrator(ABC):
    MODEL = "gemini-pro"

    @classproperty
    @abstractmethod
    def kind(cls):
        pass

    @abstractmethod
    def user_session_exist(self, uuid: str) -> bool:
        """Check if user session exist."""
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def user_session_create(self, session: dict[str, Any]):
        """Create user session for orchestrator."""
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def user_session_invoke(self, uuid: str, prompt: str) -> dict[str, Any]:
        """Invoke user session and return a response from llm orchestrator."""
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    def user_session_reset(self, session: dict[str, Any], uuid: str):
        """Reset and clear history from user session."""
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    def get_user_session(self, uuid: str) -> Any:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def user_session_insert_ticket(self, uuid: str, params: str) -> Any:
        raise NotImplementedError("Subclass should implement this!")

    @abstractmethod
    async def user_session_signout(self, uuid: str):
        """Sign out from user session. Clear and restart session."""
        raise NotImplementedError("Subclass should implement this!")

    def set_user_session_header(self, uuid: str, user_id_token: str):
        user_session = self.get_user_session(uuid)
        def get_id_token_header():
            return f"Bearer {user_id_token}"
        user_session.headers["User-Id-Token"] = get_id_token_header

    def get_user_id_token(self, uuid: str) -> Optional[str]:
        if self.user_session_exist(uuid):
            user_session = self.get_user_session(uuid)
            if user_session.headers and "User-Id-Token" in user_session.headers:
                token = user_session.headers["User-Id-Token"]()
                parts = str(token).split(" ")
                if len(parts) != 2 or parts[0] != "Bearer":
                    raise Exception("Invalid ID token")
                return parts[1]
        return None


def createOrchestrator(orchestration_type: str) -> "BaseOrchestrator":
    for cls in BaseOrchestrator.__subclasses__():
        s = f"{orchestration_type} == {cls.kind}"
        if orchestration_type == cls.kind:
            return cls()  # type: ignore
    raise TypeError(f"No orchestration type of kind {orchestration_type}")
