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

import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown import markdown
from google.oauth2 import id_token
from agent import init_agent
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport import requests
import yaml
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI app startup event
    print("Loading application...")
    yield
    # FastAPI app shutdown event
    close_client_tasks = [
        asyncio.create_task(c.client.close()) for c in user_agents.values()
    ]

    asyncio.gather(*close_client_tasks)


# FastAPI setup
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
BASE_HISTORY = [{"role": "assistant", "content": "How can I help you?"}]

# Authentication

CONFIG_FILE_PATH = "./config.yml"
GOOGLE_REDIRECT_URI = "http://localhost:8081/login/google"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AppConfig(BaseModel):
    google_client_id: str


def parse_config(path: str) -> AppConfig:
    with open(path, "r") as file:
        config = yaml.safe_load(file)
    return AppConfig(**config)


@app.route("/", methods=["GET", "POST"])
def index(request: Request):
    """Render the default template."""
    if "uuid" not in request.session:
        request.session["uuid"] = str(uuid.uuid4())
        request.session["messages"] = BASE_HISTORY
    # Agent setup
    if request.session["uuid"] in user_agents:
        user_agent = user_agents[request.session["uuid"]]
    else:
        user_agent = await init_agent()
        user_agents[request.session["uuid"]] = user_agent
    return templates.TemplateResponse(
        "index.html", {"request": request, "messages": request.session["messages"]}
    )


@app.post("/login/google")
async def login_google(
    request: Request,
):
    form_data = await request.form()
    token = form_data.get("credential", "")
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        os.environ["USER_ID_TOKEN"] = token

        # Init a new agent
        agent = init_agent()
        agents[request.session["uuid"]] = agent

        # Redirect to source URL
        source_url = request.headers.get("Referer")
        if source_url:
            return RedirectResponse(url=source_url)
        else:
            return RedirectResponse(url=GOOGLE_REDIRECT_URI)
    except ValueError:
        print("Invalid token")


@app.post("/chat", response_class=PlainTextResponse)
async def chat_handler(request: Request, prompt: str = Body(embed=True)):
    """Handler for LangChain chat requests"""
    # Retrieve user prompt
    if not prompt:
        raise HTTPException(status_code=400, detail="Error: No user query")

    if "uuid" not in request.session:
        raise HTTPException(
            status_code=400, detail="Error: Invoke index handler before start chatting"
        )

    # Add user message to chat history
    request.session["messages"] += [{"role": "user", "content": prompt}]

    user_agent = user_agents[request.session["uuid"]]
    try:
        # Send prompt to LLM
        response = await user_agent.agent.ainvoke({"input": prompt})
        request.session["messages"] += [
            {"role": "assistant", "content": response["output"]}
        ]
        # Return assistant response
        return markdown(response["output"])
    except Exception as err:
        print(err)
        raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")


@app.post("/reset")
async def reset(request: Request):
    """Reset agent"""
    global user_agents
    uuid = request.session["uuid"]

    if uuid not in user_agents.keys():
        raise HTTPException(status_code=500, detail=f"Current agent not found")

    await user_agents[uuid].client.close()
    del user_agents[uuid]
    request.session.clear()


if __name__ == "__main__":
    set_env()
    PORT = int(os.getenv("PORT", default=8081))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
