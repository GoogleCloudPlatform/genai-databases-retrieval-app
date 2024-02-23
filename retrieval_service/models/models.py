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
    sunday_start_hour: Optional[datetime.time] = None
    sunday_end_hour: Optional[datetime.time] = None
    monday_start_hour: Optional[datetime.time] = None
    monday_end_hour: Optional[datetime.time] = None
    tuesday_start_hour: Optional[datetime.time] = None
    tuesday_end_hour: Optional[datetime.time] = None
    wednesday_start_hour: Optional[datetime.time] = None
    wednesday_end_hour: Optional[datetime.time] = None
    thursday_start_hour: Optional[datetime.time] = None
    thursday_end_hour: Optional[datetime.time] = None
    friday_start_hour: Optional[datetime.time] = None
    friday_end_hour: Optional[datetime.time] = None
    saturday_start_hour: Optional[datetime.time] = None
    saturday_end_hour: Optional[datetime.time] = None
    content: Optional[str] = None
    embedding: Optional[list[float]] = None

    @field_validator(
        "sunday_start_hour",
        "sunday_end_hour",
        "monday_start_hour",
        "monday_end_hour",
        "tuesday_start_hour",
        "tuesday_end_hour",
        "wednesday_start_hour",
        "wednesday_end_hour",
        "thursday_start_hour",
        "thursday_end_hour",
        "friday_start_hour",
        "friday_end_hour",
        "saturday_start_hour",
        "saturday_end_hour",
        mode="before",
    )
    def replace_none(cls, v):
        return v or None

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


class Ticket(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime.datetime
    arrival_time: datetime.datetime
