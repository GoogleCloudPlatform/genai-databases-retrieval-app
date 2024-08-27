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

import json
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

from orchestrator import createOrchestrator

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

    # check if token and user info is still valid
    if "uuid" in session:
        user_id_token = orchestrator.get_user_id_token(session["uuid"])
        if user_id_token:
            if session.get("user_info") and not get_user_info(
                user_id_token, request.app.state.client_id
            ):
                await logout_google(request)
        elif not user_id_token and "user_info" in session:
            await logout_google(request)

    if "uuid" not in session or not orchestrator.user_session_exist(session["uuid"]):
        await orchestrator.user_session_create(session)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "messages": request.session["history"],
            "client_id": request.app.state.client_id,
            "user_img": (
                request.session["user_info"]["user_img"]
                if "user_info" in request.session
                else None
            ),
            "user_name": (
                request.session["user_info"]["name"]
                if "user_info" in request.session
                else None
            ),
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
    orchestrator.set_user_session_header(session["uuid"], str(user_id_token))
    print("Logged in to Google.")

    welcome_text = (
        f"Welcome to Cymbal Air, {session['user_info']['name']}! How may I assist you?"
    )
    if len(request.session["history"]) == 1:
        session["history"][0] = {
            "type": "ai",
            "data": {"content": welcome_text},
        }
    else:
        session["history"].append({"type": "ai", "data": {"content": welcome_text}})

    # Redirect to source URL
    source_url = request.headers["Referer"]
    return RedirectResponse(url=source_url)


@routes.post("/logout/google")
async def logout_google(
    request: Request,
):
    """Logout google account from user session and clear user session"""
    if "uuid" not in request.session:
        raise HTTPException(status_code=400, detail="No session to reset.")

    uuid = request.session["uuid"]
    orchestrator = request.app.state.orchestrator
    if orchestrator.user_session_exist(uuid):
        await orchestrator.user_session_signout(uuid)
    request.session.clear()


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
    response = await orchestrator.user_session_invoke(request.session["uuid"], prompt)
    output = response.get("output")
    confirmation = response.get("confirmation")
    trace = response.get("trace")
    # Return assistant response
    if confirmation:
        return json.dumps(
            {"type": "confirmation", "content": confirmation, "trace": trace}
        )
    else:
        request.session["history"].append({"type": "ai", "data": {"content": output}})
        return json.dumps(
            {"type": "message", "content": markdown(output), "trace": trace}
        )


@routes.post("/book/flight", response_class=PlainTextResponse)
async def book_flight(request: Request, params: str = Body(embed=True)):
    """Handler for LangChain chat requests"""
    # Retrieve the params for the booking
    if not params:
        raise HTTPException(status_code=400, detail="Error: No booking params")
    if "uuid" not in request.session:
        raise HTTPException(
            status_code=400, detail="Error: Invoke index handler before start chatting"
        )
    orchestrator = request.app.state.orchestrator
    response = await orchestrator.user_session_insert_ticket(
        request.session["uuid"], params
    )
    # Note in the history, that the ticket has been successfully booked
    request.session["history"].append(
        {"type": "ai", "data": {"content": "I have booked your ticket."}}
    )
    return response


@routes.post("/book/flight/decline", response_class=PlainTextResponse)
async def decline_flight(request: Request):
    """Handler for LangChain chat requests"""
    # Note in the history, that the ticket was not booked
    # This is helpful in case of reloads so there doesn't seem to be a break in communication.
    orchestrator = request.app.state.orchestrator
    response = await orchestrator.user_session_decline_ticket(request.session["uuid"])
    request.session["history"].append(
        {"type": "ai", "data": {"content": "Please confirm if you would like to book."}}
    )
    request.session["history"].append(
        {"type": "human", "data": {"content": "I changed my mind."}}
    )
    return None


@routes.post("/reset")
def reset(request: Request):
    """Reset user session"""

    if "uuid" not in request.session:
        raise HTTPException(status_code=400, detail="No session to reset.")

    uuid = request.session["uuid"]
    orchestrator = request.app.state.orchestrator
    if not orchestrator.user_session_exist(uuid):
        raise HTTPException(status_code=500, detail="Current user session not found")

    orchestrator.user_session_reset(request.session, uuid)


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


def clear_user_info(session: dict[str, Any]):
    del session["user_info"]


def init_app(
    orchestration_type: Optional[str],
    client_id: Optional[str],
    middleware_secret: Optional[str],
) -> FastAPI:
    # FastAPI setup
    if orchestration_type is None:
        raise HTTPException(status_code=500, detail="Orchestrator not found")
    app = FastAPI(lifespan=lifespan)
    app.state.client_id = client_id
    app.state.orchestrator = createOrchestrator(orchestration_type)
    app.include_router(routes)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.add_middleware(SessionMiddleware, secret_key=middleware_secret)
    return app


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", default=8081))
    HOST = os.getenv("HOST", default="0.0.0.0")
    ORCHESTRATION_TYPE = os.getenv("ORCHESTRATION_TYPE", default="langchain-tools")
    CLIENT_ID = os.getenv("CLIENT_ID")
    MIDDLEWARE_SECRET = os.getenv("MIDDLEWARE_SECRET", default="this is a secret")
    app = init_app(
        ORCHESTRATION_TYPE, client_id=CLIENT_ID, middleware_secret=MIDDLEWARE_SECRET
    )
    if app is None:
        raise TypeError("app not instantiated")
    uvicorn.run(app, host=HOST, port=PORT)
