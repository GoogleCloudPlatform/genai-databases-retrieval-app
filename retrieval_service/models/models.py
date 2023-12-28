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

import ast
import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, FieldValidationInfo, field_validator


class Airport(BaseModel):
    id: int
    iata: str
    name: str
    city: str
    country: str


class Amenity(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    name: str
    description: str
    location: str
    terminal: str
    category: str
    hour: str
    start_hours: list[str]
    end_hours: list[str]
    content: Optional[str] = None
    embedding: Optional[list[float]] = None

    @field_validator("start_hours", "end_hours", mode="before")
    def validate_hours(cls, v):
        if type(v) == str:
            v = ast.literal_eval(v)
            v = [str(f) for f in v]
        return v

    @field_validator("embedding", mode="before")
    def validate(cls, v):
        if type(v) == str:
            v = ast.literal_eval(v)
            v = [float(f) for f in v]
        return v


class Flight(BaseModel):
    id: int
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime.datetime
    arrival_time: datetime.datetime
    departure_gate: str
    arrival_gate: str
