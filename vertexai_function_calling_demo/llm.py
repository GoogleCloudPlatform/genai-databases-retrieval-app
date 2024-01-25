# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from vertexai.preview.generative_models import ChatSession, GenerativeModel, GenerationResponse
from google.protobuf.json_format import MessageToDict
from functions import assistant_tool


MODEL = "gemini-pro"
BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
chat_assistants: Dict[str, ChatAssistant] = {}

# aiohttp context
connector = None

class ChatAssistant:
    client: aiohttp.ClientSession
    chat: ChatSession

    def __init__(self, client, chat: ChatSession) -> None:
        self.client = client
        self.chat = chat

    def invoke(self, prompt: str):
        model_response = self.request_chat_model(prompt)
        function_response = self.request_function(model_response)

    def request_chat_model(self, prompt: str) -> Union:
        model_response = self.chat.send_message(prompt)
        return model_response

    async def request_function(self, model_response):
        function_call = MessageToDict(model_response.candidates[0].content.parts[0].function_call._pb)
        function_name = function_call['name']
        params = function_call['args']
        async with aiohttp.ClientSession() as client:
            response = await client.get(
                url=f"{BASE_URL}/{function_name}",
                params=params,
                headers=get_headers(self.client),
            }
            response = await response.json()
            return response


async def get_connector():
    global connector
    if connector is None:
        connector = aiohttp.TCPConnector(limit=100)
    return connector


async def handle_error_response(response):
    if response.status != 200:
        return f"Error sending {response.method} request to {str(response.url)}): {await response.text()}"


async def create_client_session(user_id_token: Optional[str]) -> aiohttp.ClientSession:
    headers = {}
    if user_id_token is not None:
        # user-specific query authentication
        headers["User-Id-Token"] = user_id_token

    return aiohttp.ClientSession(
        connector=await get_connector(),
        connector_owner=False,
        headers=headers,
        raise_for_status=handle_error_response,
    )

async def init_chat_assistant(user_id_token) -> ChatAssistant:
    print("Initializing agent..")
    client = await create_client_session(user_id_token)
    model = GenerativeModel(MODEL, tools=[assistant_tool()])
    func_calling_chat = model.start_chat()
    return ChatAssistant(client, func_calling_chat)
