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

import os
from contextlib import asynccontextmanager
from typing import Any, Optional

import uvicorn
from fastapi import APIRouter, Body, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.auth.transport import requests  # type:ignore
from google.oauth2 import id_token  # type:ignore
from markdown import markdown
from starlette.middleware.sessions import SessionMiddleware

from orchestrator import BaseOrchestrator, createOrchestrator

routes = APIRouter()
templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI app startup event
    print("Loading application...")
    yield
    # FastAPI app shutdown event
    app.state.orchestrator.close_clients()


@routes.get("/")
@routes.post("/")
async def index(request: Request):
    """Render the default template."""
    # User session setup
    orchestrator = request.app.state.orchestrator
    session = request.session

    if "uuid" not in session or not orchestrator.user_session_exist(session["uuid"]):
        await orchestrator.user_session_create(session)

    # recheck if token is still valid
    user_id_token = orchestrator.get_user_id_token(session["uuid"])
    if user_id_token:
        check_user_info_validity(session, user_id_token, request.app.state.client_id)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "messages": request.session["history"],
            "client_id": request.app.state.client_id,
            "user_img": request.session["user_info"]["user_img"]
            if "user_info" in request.session
            else None,
        },
    )


@routes.post("/login/google", response_class=RedirectResponse)
async def login_google(
    request: Request,
):
    form_data = await request.form()
    user_id_token = form_data.get("credential")
    if user_id_token is None:
        raise HTTPException(status_code=401, detail="No user credentials found")

    client_id = request.app.state.client_id
    if not client_id:
        raise HTTPException(status_code=400, detail="Client id not found")

    session = request.session
    user_info = get_user_info(str(user_id_token), client_id)
    session["user_info"] = user_info

    # create new request session
    orchestrator = request.app.state.orchestrator
    orchestrator.set_user_session_header(request.session["uuid"], str(user_id_token))
    print("Logged in to Google.")

    welcome_text = f"Welcome to Cymbal Air, {request.session['user_info']['name']}! How may I assist you?"
    if len(request.session["history"]) == 1:
        request.session["history"][0] = {
            "type": "ai",
            "data": {"content": welcome_text},
        }
    else:
        request.session["history"].append(
            {"type": "ai", "data": {"content": welcome_text}}
        )

    # Redirect to source URL
    source_url = request.headers["Referer"]
    return RedirectResponse(url=source_url)


@routes.post("/chat", response_class=PlainTextResponse)
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
    request.session["history"].append({"type": "human", "data": {"content": prompt}})
    orchestrator = request.app.state.orchestrator
    output = await orchestrator.user_session_invoke(request.session["uuid"], prompt)
    # Return assistant response
    request.session["history"].append({"type": "ai", "data": {"content": output}})
    return markdown(output)


@routes.post("/reset")
async def reset(request: Request):
    """Reset user session"""

    if "uuid" not in request.session:
        raise HTTPException(status_code=400, detail=f"No session to reset.")

    uuid = request.session["uuid"]
    orchestrator = request.app.state.orchestrator
    if not orchestrator.user_session_exist(uuid):
        raise HTTPException(status_code=500, detail=f"Current user session not found")

    await orchestrator.user_session_reset(uuid)
    request.session.clear()


def get_user_info(user_id_token: str, client_id: str) -> dict[str, str]:
    try:
        id_info = id_token.verify_oauth2_token(
            user_id_token, requests.Request(), audience=client_id
        )
        return {
            "user_img": id_info["picture"],
            "name": id_info["name"],
        }
    except ValueError as err:
        return {}


def check_user_info_validity(session: dict[str, Any], user_id_token: str, client_id: str):
    if not get_user_info(user_id_token, client_id):
        del session["user_info"]


def init_app(
    orchestration_type: Optional[str],
    client_id: Optional[str],
    secret_key: Optional[str],
) -> FastAPI:
    # FastAPI setup
    if orchestration_type is None:
        raise HTTPException(status_code=500, detail="Orchestrator not found")
    app = FastAPI(lifespan=lifespan)
    app.state.client_id = client_id
    app.state.orchestrator = createOrchestrator(orchestration_type)
    app.include_router(routes)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.add_middleware(SessionMiddleware, secret_key=secret_key)
    return app


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", default=8081))
    HOST = os.getenv("HOST", default="0.0.0.0")
    ORCHESTRATION_TYPE = os.getenv("ORCHESTRATION_TYPE")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRET_KEY = os.getenv("SECRET_KEY")
    app = init_app(ORCHESTRATION_TYPE, client_id=CLIENT_ID, secret_key=SECRET_KEY)
    if app is None:
        raise TypeError("app not instantiated")
    uvicorn.run(app, host=HOST, port=PORT)
