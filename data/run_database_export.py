# Copyright 2025 Google LLC
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
import csv
import json

from toolbox_core import ToolboxClient
from toolbox_core.tool import ToolboxTool

from agent.tools import TOOLBOX_URL
from models import Airport, Amenity, Flight, Policy


async def export_data() -> tuple[
    list[Airport],
    list[Amenity],
    list[Flight],
    list[Policy],
]:
    async with ToolboxClient(TOOLBOX_URL) as toolbox:
        execute_sql = await toolbox.load_tool("execute_sql")
        airport_results, amenity_results, flights_results, policy_results = (
            await asyncio.gather(
                execute_sql("""SELECT * FROM airports ORDER BY id ASC"""),
                execute_sql("""SELECT * FROM amenities ORDER BY id ASC"""),
                execute_sql("""SELECT * FROM flights ORDER BY id ASC"""),
                execute_sql("""SELECT * FROM policies ORDER BY id ASC"""),
            )
        )

    airports = [Airport.model_validate(a) for a in json.loads(airport_results)]
    amenities = [Amenity.model_validate(a) for a in json.loads(amenity_results)]
    flights = [Flight.model_validate(f) for f in json.loads(flights_results)]
    policies = [Policy.model_validate(p) for p in json.loads(policy_results)]

    return airports, amenities, flights, policies


async def export_dataset(
    airports: list[Airport],
    amenities: list[Amenity],
    flights: list[Flight],
    policies: list[Policy],
    airports_new_path: str,
    amenities_new_path: str,
    flights_new_path: str,
    policies_new_path: str,
) -> None:
    with open(airports_new_path, "w") as f:
        col_names = ["id", "iata", "name", "city", "country"]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for airport in airports:
            writer.writerow(airport.model_dump())

    with open(amenities_new_path, "w") as f:
        col_names = [
            "id",
            "name",
            "description",
            "location",
            "terminal",
            "category",
            "hour",
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
            "content",
            "embedding",
        ]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for amenity in amenities:
            writer.writerow(amenity.model_dump())

    with open(flights_new_path, "w") as f:
        col_names = [
            "id",
            "airline",
            "flight_number",
            "departure_airport",
            "arrival_airport",
            "departure_time",
            "arrival_time",
            "departure_gate",
            "arrival_gate",
        ]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for fl in flights:
            writer.writerow(fl.model_dump())

    with open(policies_new_path, "w") as f:
        col_names = [
            "id",
            "content",
            "embedding",
        ]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for p in policies:
            writer.writerow(p.model_dump())


async def main():
    airports, amenities, flights, policies = await export_data()

    airports_new_path = "data/airport_dataset.csv.new"
    amenities_new_path = "data/amenity_dataset.csv.new"
    flights_new_path = "data/flights_dataset.csv.new"
    policies_new_path = "data/cymbalair_policy.csv.new"

    await export_dataset(
        airports,
        amenities,
        flights,
        policies,
        airports_new_path,
        amenities_new_path,
        flights_new_path,
        policies_new_path,
    )

    print("database export done.")


if __name__ == "__main__":
    asyncio.run(main())
