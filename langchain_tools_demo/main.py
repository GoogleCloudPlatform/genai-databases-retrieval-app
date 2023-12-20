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
from google.oauth2 import id_token
from markdown import markdown
from starlette.middleware.sessions import SessionMiddleware

from agent import init_agent, user_agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI app startup event
    print("Loading application...")
    yield
    # FastAPI app shutdown event
    close_client_tasks = [
        asyncio.create_task(a.client.close()) for a in user_agents.values()
    ]

    asyncio.gather(*close_client_tasks)


# FastAPI setup
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
# TODO: set secret_key for production
app.add_middleware(SessionMiddleware, secret_key="SECRET_KEY")
templates = Jinja2Templates(directory="templates")
BASE_HISTORY = [{"role": "assistant", "content": "How can I help you?"}]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
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
    request.session.clear()
    form_data = await request.form()
    user_id_token = form_data.get("credential", "")

    user_agent = await init_agent(user_id_token)
    user_agents[request.session["uuid"]] = user_agent

    # Redirect to source URL
    source_url = request.headers.get("Referer")
    return RedirectResponse(url=source_url)


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
    PORT = int(os.getenv("PORT", default=8081))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
