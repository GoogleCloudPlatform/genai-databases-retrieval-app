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
<<<<<<< HEAD
    airports_ds_path = "../data/airport_dataset.csv"
    amenities_ds_path = "../data/amenity_dataset.csv"
    flights_ds_path = "../data/flights_dataset.csv"
=======
<<<<<<< HEAD
    bucket_path = "cloud-samples-data"
    airports_blob_path = "databases-golden-demo/airport_dataset.csv"
    amenities_blob_path = "databases-golden-demo/amenity_dataset.csv"
    flights_blob_path = "databases-golden-demo/flights_dataset.csv"
    tickets_blob_path = "databases-golden-demo/tickets_dataset.csv"
    seats_blob_path = "databases-golden-demo/seats_dataset.csv"
>>>>>>> 07736b2 (add policy to vector store)

    cfg = parse_config("config.yml")
    ds = await datastore.create(cfg.datastore)
    airports, amenities, flights = await ds.load_dataset(
        airports_ds_path, amenities_ds_path, flights_ds_path
    )
<<<<<<< HEAD
    await ds.initialize_data(airports, amenities, flights)
=======
    await ds.initialize_data(airports, amenities, flights, tickets, seats)
=======
    airports_ds_path = "../data/airport_dataset.csv"
    amenities_ds_path = "../data/amenity_dataset.csv"
    flights_ds_path = "../data/flights_dataset.csv"
    policies_ds_path = "../data/cymbalair_policy.csv"

    cfg = parse_config("config.yml")
    ds = await datastore.create(cfg.datastore)
    airports, amenities, flights, policies = await ds.load_dataset(
        airports_ds_path, amenities_ds_path, flights_ds_path, policies_ds_path
    )
    await ds.initialize_data(airports, amenities, flights, policies)
>>>>>>> 5129879 (add policy to vector store)
>>>>>>> 07736b2 (add policy to vector store)
    await ds.close()

    print("database init done.")


if __name__ == "__main__":
    asyncio.run(main())
