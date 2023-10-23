import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from markdown import markdown
from starlette.middleware.sessions import SessionMiddleware
import uuid
import uvicorn
from agent import init_agent

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# TODO: set secret_key for production
app.add_middleware(SessionMiddleware, secret_key="SECRET_KEY")
templates = Jinja2Templates(directory="templates")

agents = {}
BASE_HISTORY = [{"role": "assistant", "content": "How can I help you?"}]


class Prompt(BaseModel):
    """Chat handler request object"""

    prompt: str


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Render the default template."""
    request.session.clear()
    if "uuid" not in request.session:
        request.session["uuid"] = str(uuid.uuid4())
        request.session["messages"] = BASE_HISTORY
    return templates.TemplateResponse(
        "index.html", {"request": request, "messages": request.session["messages"]}
    )


@app.post("/chat", response_class=PlainTextResponse)
def chat_handler(prompt: Prompt, request: Request):
    """Handler for LangChain chat requests"""
    # Retrieve user prompt
    if not prompt and not prompt.prompt:
        raise HTTPException(status_code=400, detail="Error: No user query")

    content = prompt.prompt
    # Add user message to chat history
    request.session["messages"] += [{"role": "user", "content": content}]
    # Agent setup
    if "uuid" in request.session and request.session["uuid"] in agents:
        agent = agents[request.session["uuid"]]
    else:
        agent = init_agent(request.session["messages"])
        agents[request.session["uuid"]] = agent
    try:
        # Send prompt to LLM
        response = agent.invoke({"input": content})
        request.session["messages"] += [
            {"role": "assistant", "content": response["output"]}
        ]
        # Return assistant response
        print(agent.agent.llm_chain.memory)
        return markdown(response["output"])
    except Exception as err:
        print(err)
        raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")


if __name__ == "__main__":
    PORT = int(os.getenv("PORT")) if os.getenv("PORT") else 8080
    uvicorn.run(app, host="0.0.0.0", port=PORT)
