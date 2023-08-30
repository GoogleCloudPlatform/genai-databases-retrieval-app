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

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, TypeVar

import models


class AbstractConfig(ABC):
    kind: str


class Client(ABC):
    @classmethod
    @property
    @abstractmethod
    def kind(cls):
        pass

    @classmethod
    @abstractmethod
    async def create(cls, config: AbstractConfig) -> "Client":
        pass

    @classmethod
    @abstractmethod
    async def initialize_data(
        cls, toys: List[models.Toy], embeddings: List[models.Embedding]
    ) -> None:
        pass

    @classmethod
    @abstractmethod
    async def export_data(cls) -> Tuple[List[models.Toy], List[models.Embedding]]:
        pass

    @classmethod
    @abstractmethod
    async def semantic_similiarity_search(
        cls, query_embedding: List[float], similarity_theshold: float, top_k: int
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("Subclass should implement this!")

    @classmethod
    @abstractmethod
    async def close(cls):
        pass


async def create(config: AbstractConfig) -> Client:
    for cls in Client.__subclasses__():
        if config.kind == cls.kind:
            return await cls.create(config)  # type: ignore
    raise TypeError(f"No clients of kind '{config.kind}'")
