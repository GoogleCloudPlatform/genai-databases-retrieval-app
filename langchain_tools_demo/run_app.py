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

import requests
import streamlit as st

from langchain.llms import VertexAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool


st.title("Database Extension Testing")


def find_similar_toys(desc: str) -> str:
    params = {"top_k": "5", "query": desc}
    response = requests.get("http://127.0.0.1:8080/semantic_similiarity_search", params)

    if response.status_code != 200:
        return f"Error trying to find similar toys: {response.text}"

    results = [
        "Here are is list of toys related to the query in JSON format. Only use this list in making recommendations to the customer. "
    ] + [f"{r}" for r in response.json()]
    if len(results) <= 1:
        return "There are no toys matching that query. Please try again or let the user know there are no results."
    output = "\n".join(results)
    # print(results)
    return output


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    tools = [
        Tool.from_function(
            name="find_similar_toys",
            func=find_similar_toys,
            description="useful when you need a toy recommendation. Returns several toys that are related to the query. Only recommend toys that are returned by this query.",
        ),
    ]
    llm = VertexAI(max_output_tokens=512, verbose=True)
    memory = ConversationBufferMemory(memory_key="chat_history")
    st.session_state.agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
    )
    st.session_state.agent.agent.llm_chain.verbose = True  # type: ignore

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = st.session_state.agent.invoke({"input": prompt})
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response["output"])
    # Add assistant response to chat history
    st.session_state.messages.append(
        {"role": "assistant", "content": response["output"]}
    )
