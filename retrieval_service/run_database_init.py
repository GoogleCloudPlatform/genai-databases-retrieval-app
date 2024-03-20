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

import argparse
import asyncio

import datastore
import models
from app import parse_config


async def main(load_all_data: bool = False) -> None:
    bucket_path = "cloud-samples-data"
    flights_blob_path = "databases-golden-demo/flights_dataset.csv"
    tickets_blob_path = "databases-golden-demo/tickets_dataset.csv"
    seats_blob_path = "databases-golden-demo/seats_dataset.csv"

    airports_ds_path = "../data/airport_dataset.csv"
    amenities_ds_path = "../data/amenity_dataset.csv"

    cfg = parse_config("config.yml")
    ds = await datastore.create(cfg.datastore)
    airports, amenities, flights_streamer, tickets_streamer, seats_streamer = (
        await ds.load_dataset(
            bucket_path,
            airports_ds_path,
            amenities_ds_path,
            flights_blob_path,
            tickets_blob_path,
            seats_blob_path,
            load_all_data,
        )
    )
    await ds.initialize_data(
        airports, amenities, flights_streamer, tickets_streamer, seats_streamer
    )
    await ds.close()

    print("database init done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--load-all-data",
        action="store_true",
        help="Whether or not to load all the data from GCS. This may take a long time.",
    )
    args = parser.parse_args()
    asyncio.run(main(args.load_all_data))
