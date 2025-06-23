# Copyright 2024 Google LLC
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

import time

import pandas as pd
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app import EMBEDDING_MODEL_NAME


def main() -> None:
    policies_ds_path = "./data/cymbalair_policy.csv"

    chunked = text_split(_POLICY)
    data_embeddings = vectorize(chunked)
    data_embeddings.to_csv(policies_ds_path, index=True, index_label="id")

    print("Done generating policy dataset.")


def text_split(data):
    headers_to_split_on = [("#", "Header 1"), ("##", "Header 2")]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=False
    )
    md_header_splits = markdown_splitter.split_text(data)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=30,
        length_function=len,
    )
    splits = text_splitter.split_documents(md_header_splits)

    chunked = [{"content": s.page_content} for s in splits]
    return chunked


def vectorize(chunked):
    embed_service = VertexAIEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    def retry_with_backoff(func, *args, retry_delay=5, backoff_factor=2, **kwargs):
        max_attempts = 3
        retries = 0
        for i in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"error: {e}")
                retries += 1
                wait = retry_delay * (backoff_factor**retries)
                print(f"Retry after waiting for {wait} seconds...")
                time.sleep(wait)

    batch_size = 1
    for i in range(0, len(chunked), batch_size):
        request = [x["content"] for x in chunked[i : i + batch_size]]
        response = retry_with_backoff(embed_service.embed_documents, request)
        # Store the retrieved vector embeddings for each chunk back.
        for x, e in zip(chunked[i : i + batch_size], response):
            x["embedding"] = e

    data_embeddings = pd.DataFrame(chunked)
    data_embeddings.head()
    return data_embeddings


_POLICY = """# Cymbal Air: Passenger Policy
## Ticket Purchase and Changes
Types of Fares: Cymbal Air offers a variety of fares (Economy, Premium Economy, Business Class, and First Class). Fare restrictions, such as change fees and refundability, vary depending on the fare purchased.
Changes: Changes to tickets are permitted at any time until 60 minutes prior to scheduled departure. There are no fees for changes as long as the new ticket is on Cymbal Air and is at an equal or lower price.  If the new ticket has a higher price, the customer must pay the difference between the new and old fares.  Changes to a non-Cymbal-Air flight include a $100 change fee.
Cancellations: Fully refundable tickets can be canceled at any time until 60 minutes prior to scheduled departure for a full refund.  For non-refundable tickets, there will be no cost associated with cancellation within 24 hours of ticket purchase. After 24 hours of ticket purchase, there will be a $200 fee for ticket cancellation. Cancellations less than 24 hours before scheduled departure receive no refund.
Payment of refunds: refunds for fully refundable tickets will be returned to the original method of payment within 3-5 business days.  Refunds for non-refundable tickets, less fees, will be refunded in the form of a trip credit which can be applied to future Cymbal Air flights.
## Baggage
Checked Baggage: Economy passengers are allowed 2 checked bags. Business class and First class passengers are allowed 4 checked bags. Additional baggage will cost $70 and a $30 fee applies for all checked bags over 50 lbs. Cymbal Air cannot accept checked bags over 100 lbs. We only accept checked bags up to 115 inches in total dimensions (length + width + height), and oversized baggage will cost $30. Checked bags above 160 inches in total dimensions will not be accepted.
Carry-on Baggage: Passengers are allowed one carry-on bag and one personal item. These items must meet size and weight restrictions.
Liability: Cymbal Air assumes limited liability for lost, damaged, or delayed baggage. Passengers are encouraged to purchase travel insurance for additional protection.
## Check-in and Boarding
Check-in: Passengers are advised to check in online or at the airport kiosk within the specified timeframes before departure. Check-in deadlines are 1 hour prior to departure time.
Boarding: Boarding will begin approximately 30 minutes prior to departure. Passengers must present a valid boarding pass and government-issued ID.
Gate Closure: Boarding gates close 10 minutes prior to departure. Late passengers may not be permitted to board.
## Special Assistance
Passengers with Disabilities: Cymbal Air is committed to providing accommodations for passengers with disabilities. Please contact us at least 48 hours before departure to arrange assistance.
Unaccompanied Minors: We offer an unaccompanied minor program for children traveling alone. Fees apply. Contact us for details.
Traveling with Pets: Pets may be allowed in the cabin or as checked baggage depending on size and breed. Fees and restrictions apply. Please consult our website.
##  Overbooking
In the rare event of an overbooked flight, Cymbal Air will first seek volunteers to give up their seats in exchange for compensation. If insufficient volunteers are found, passengers may be denied boarding involuntarily in accordance with our overbooking policy.
## Flight Delays and Cancellations
Cymbal Air strives to maintain on-time performance, but disruptions due to weather, mechanical issues, or other events may occur. In the event of delays or cancellations:
Rebooking: We will make reasonable efforts to rebook affected passengers on the next available flight.
Compensation: Compensation may be provided in certain situations as outlined by our policies and regulations.
"""

if __name__ == "__main__":
    main()
