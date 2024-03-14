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
import models
from app import parse_config


async def main() -> None:
    bucket_path = "cloud-samples-data"
    airports_blob_path = "databases-golden-demo/airport_dataset.csv"
    amenities_blob_path = "databases-golden-demo/amenity_dataset.csv"
    flights_blob_path = "databases-golden-demo/flights_dataset.csv"
    tickets_blob_path = "databases-golden-demo/tickets_dataset.csv"
    seats_blob_path = "databases-golden-demo/seats_dataset.csv"

    cfg = parse_config("config.yml")
    ds = await datastore.create(cfg.datastore)
    airports, amenities, flights, tickets, seats = await ds.load_dataset(
        bucket_path,
        airports_blob_path,
        amenities_blob_path,
        flights_blob_path,
        tickets_blob_path,
        seats_blob_path,
    )
    await ds.initialize_data(airports, amenities, flights, tickets, seats)
    await ds.close()

    print("database init done.")


if __name__ == "__main__":
    asyncio.run(main())
