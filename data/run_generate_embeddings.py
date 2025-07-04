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

from langchain_google_vertexai import VertexAIEmbeddings

import models
from app import EMBEDDING_MODEL_NAME


async def main() -> None:
    embed_service = VertexAIEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    amenities: list[models.Amenity] = []
    with open("./amenity_dataset.csv", "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        for line in reader:
            amenity = models.Amenity.model_validate(line)
            if amenity.content:
                amenity.embedding = embed_service.embed_query(amenity.content)
                amenities.append(amenity)

    policies: list[models.Policy] = []
    with open("./cymbalair_policy.csv", "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        for line in reader:
            policy = models.Policy.model_validate(line)
            if policy.content:
                policy.embedding = embed_service.embed_query(policy.content)
                policies.append(policy)

    print("Completed embedding generation.")

    with open("./amenity_dataset.csv.new", "w") as f:
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

    with open("./cymbalair_policy.csv.new", "w") as f:
        col_names = [
            "id",
            "content",
            "embedding",
        ]
        writer = csv.DictWriter(f, col_names, delimiter=",")
        writer.writeheader()
        for policy in policies:
            writer.writerow(policy.model_dump())

    print("Wrote data to CSV.")


if __name__ == "__main__":
    asyncio.run(main())
