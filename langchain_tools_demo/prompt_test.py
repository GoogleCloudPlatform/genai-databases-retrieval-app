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

import pytest

from agent import init_agent

questions = [
    # Flights
    "What gate is flight 118 at?",
    "What is the status of flight 118? ",
    "What is the status of flight 188? ",
    "What gate is flight UA 1532 at?",
    "What is the status of flight UA 1532? ",
    "What time is my flight leaving today?",
    "What flights are departing SFO?",
    "what flights leave SEA on 11-01-2023?",
    "What flights are leaving from SFO today?",
    "What flights are leaving from SFO on 2023-11-01?",
    "What flights land at SFO today?",
    "What flights arrive at SFO today?",
    "What flights arrive at SFO tomorrow?",
    "Find flights that leave SFO and arrive at SEA",
    "Where does flight 118 land?",
    "What gate does flight 118 land?",
    "What gate does flight UA 1532 land?",
    # Amenities
    "Where can I get coffee near gate A6?",
    "Where can I get a snack near the gate for flight 457?",
    "Where can I get a snack near the gate for flight UA1739?",
    "I need a gift",
    "Where is Starbucks?",
    "What are the hours of Amy's Drive Thru?",
    "Where can I get a salad in Terminal 1?",
    "I need headphones",
    "Are there restaurants open at midnight?",
    "Where can I buy a luxury bag?",
    # Airports
    "Where is SFO?",
    "Where is the san Prancisco airport?",
    "What is the code for San Francisco airport?",
    "What is the YWG airport?",
    # Extra
    "hi",
    "How can you help me?",
    "Where are the restrooms?",
    "what are airport hours?",
    "Where is TSA pre-check?",
]


@pytest.mark.parametrize("question", questions)
def test_eval(question):
    agent = init_agent()
    response = agent.invoke({"input": question})
    results = response["output"]
    print(question, results)
    assert results
