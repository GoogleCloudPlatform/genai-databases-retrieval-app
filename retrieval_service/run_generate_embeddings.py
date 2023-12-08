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

from langchain.embeddings import VertexAIEmbeddings

import models
from app import EMBEDDING_MODEL_NAME


async def main() -> None:
    embed_service = VertexAIEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    amenities: list[models.Amenity] = []
    with open("../data/amenity_dataset.csv", "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        for line in reader:
            amenity = models.Amenity.model_validate(line)
            amenity.embedding = embed_service.embed_query(amenity.content)
            amenities.append(amenity)

    print("Completed embedding generation.")

    with open("../data/amenity_dataset.csv.new", "w") as f:
        col_names = [
            "id",
            "name",
            "description",
            "location",
            "terminal",
            "category",
            "hour",
            "content",
            "embedding",
        ]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for amenity in amenities:
            writer.writerow(amenity.model_dump())

    print("Wrote data to CSV.")


if __name__ == "__main__":
    asyncio.run(main())
