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
import csv

import numpy as np

import datastore
from app import parse_config


async def main():
    np.set_printoptions(linewidth=100000)

    cfg = parse_config("config.yml")
    ds = await datastore.create(cfg.datastore)

    toys, airports, embeddings = await ds.export_data()

    await ds.close()

    with open("data/product_dataset.csv.new", "w") as f:
        col_names = ["product_id", "product_name", "description", "list_price"]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for t in toys:
            writer.writerow(t.model_dump())

    with open("data/airport_dataset.csv.new", "w") as f:
        col_names = ["airport_id", "iata", "name", "city", "country"]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for a in airports:
            writer.writerow(a.model_dump())

    with open("data/product_embeddings_dataset.csv.new", "w") as f:
        col_names = ["product_id", "content", "embedding"]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for e in embeddings:
            writer.writerow(e.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
