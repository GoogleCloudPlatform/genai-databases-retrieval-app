# Copyright 2023 Google LLC
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

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown import markdown
from starlette.middleware.sessions import SessionMiddleware

from llm import chat_assistants, init_chat_assistant


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI app startup event
    print("Loading application...")
    yield
    # FastAPI app shutdown event
    close_client_tasks = [
        asyncio.create_task(c.client.close()) for c in chat_assistants.values()
    ]

    asyncio.gather(*close_client_tasks)


# FastAPI setup
app = FastAPI(lifespan=lifespan)
app.mount("/../static", StaticFiles(directory="../static"), name="static")
# TODO: set secret_key for production
app.add_middleware(SessionMiddleware, secret_key="SECRET_KEY")
templates = Jinja2Templates(directory="../templates")
BASE_HISTORY = [
    {"type": "ai", "data": {"content": "I am an SFO Airport Asistant, ready to assist you."}}
]
CLIENT_ID = os.getenv("CLIENT_ID")


@app.route("/", methods=["GET", "POST"])
async def index(request: Request):
    """Render the default template."""
    # Agent setup
    agent = await get_agent(request.session)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "messages": request.session["history"],
            "client_id": CLIENT_ID,
        },
    )


@app.post("/login/google", response_class=RedirectResponse)
async def login_google(
    request: Request,
):
    form_data = await request.form()
    user_id_token = form_data.get("credential")
    if user_id_token is None:
        raise HTTPException(status_code=401, detail="No user credentials found")
    # create new request session
    _ = await get_agent(request.session)
    print("Logged in to Google.")

    # Redirect to source URL
    source_url = request.headers["Referer"]
    return RedirectResponse(url=source_url)


@app.post("/chat", response_class=PlainTextResponse)
async def chat_handler(request: Request, prompt: str = Body(embed=True)):
    """Handler for chat requests"""
    # Retrieve user prompt
    if not prompt:
        raise HTTPException(status_code=400, detail="Error: No user query")
    if "uuid" not in request.session:
        raise HTTPException(
            status_code=400, detail="Error: Invoke index handler before start chatting"
        )

    # Add user message to chat history
    request.session["history"].append({"type": "human", "data": {"content": prompt}})
    chat_assistant = await get_agent(request.session)

    try:
        # Send prompt to LLM
        response = await chat_assistant.invoke(prompt)
        # Return assistant response
        request.session["history"].append({"type": "ai", "data": {"content": response["output"]}})
        return markdown(response["output"])
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")


async def get_agent(session: dict[str, Any]):
    global chat_assistants
    if "uuid" not in session:
        session["uuid"] = str(uuid.uuid4())
    id = session["uuid"]
    if "history" not in session:
        session["history"] = BASE_HISTORY
    if uuid not in chat_assistants:
        chat_assistants[id] = await init_chat_assistant(session["uuid"])
    return chat_assistants[id]


@app.post("/reset")
async def reset(request: Request):
    """Reset agent"""

    if "uuid" not in request.session:
        raise HTTPException(status_code=400, detail=f"No session to reset.")

    uuid = request.session["uuid"]
    global chat_assistants
    if uuid not in chat_assistants.keys():
        raise HTTPException(status_code=500, detail=f"Current assistant not found")

    await chat_assistants[uuid].client.close()
    del chat_assistants[uuid]
    request.session.clear()


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", default=8081))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
