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
import uuid

import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain.agents.agent import AgentExecutor
from markdown import markdown
from starlette.middleware.sessions import SessionMiddleware

from agent import init_agent

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# TODO: set secret_key for production
app.add_middleware(SessionMiddleware, secret_key="SECRET_KEY")
templates = Jinja2Templates(directory="templates")

agents: dict[str, AgentExecutor] = {}
BASE_HISTORY = [{"role": "assistant", "content": "How can I help you?"}]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Render the default template."""
    request.session.clear()  # Clear chat history, if needed
    if "uuid" not in request.session:
        request.session["uuid"] = str(uuid.uuid4())
        request.session["messages"] = BASE_HISTORY
    return templates.TemplateResponse(
        "index.html", {"request": request, "messages": request.session["messages"]}
    )


@app.post("/chat", response_class=PlainTextResponse)
async def chat_handler(request: Request, prompt: str = Body(embed=True)):
    """Handler for LangChain chat requests"""
    # Retrieve user prompt
    if not prompt:
        raise HTTPException(status_code=400, detail="Error: No user query")

    if "uuid" not in request.session:
        request.session["uuid"] = str(uuid.uuid4())
        request.session["messages"] = BASE_HISTORY

    # Add user message to chat history
    request.session["messages"] += [{"role": "user", "content": prompt}]
    # Agent setup
    if request.session["uuid"] in agents:
        agent = agents[request.session["uuid"]]
    else:
        agent = init_agent()
        agents[request.session["uuid"]] = agent
    try:
        # Send prompt to LLM
        response = await agent.ainvoke({"input": prompt})
        request.session["messages"] += [
            {"role": "assistant", "content": response["output"]}
        ]
        # Return assistant response
        print(response)
        print(response.text())
        return markdown(response["output"])
    except Exception as err:
        print(err)
        raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", default=8081))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
