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

import asyncio

import datastore
from app import parse_config


async def main():
    cfg = parse_config("config.yml")
    ds = await datastore.create(cfg.datastore)

    airports, amenities, flights, policies = await ds.export_data()

    await ds.close()

    airports_new_path = "../data/airport_dataset.csv.new"
    amenities_new_path = "../data/amenity_dataset.csv.new"
    flights_new_path = "../data/flights_dataset.csv.new"
    policies_new_path = "../data/cymbalair_policy.csv.new"

    await ds.export_dataset(
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
