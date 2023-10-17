import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain.agents import AgentType, initialize_agent
from langchain.llms import VertexAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from markdown import markdown
from starlette.middleware.sessions import SessionMiddleware
import google.auth.transport.requests
import google.oauth2.id_token
import requests
import uuid
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# TODO: set secret_key for production
app.add_middleware(SessionMiddleware, secret_key="SECRET_KEY")
templates = Jinja2Templates(directory="templates")

agents = {}
BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")
BASE_HISTORY = [{"role": "assistant", "content": "How can I help you?"}]
DEBUG = bool(os.getenv("DEBUG", default=False))


class Prompt(BaseModel):
    """Chat handler request object"""

    prompt: str


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Render the default template."""
    # request.session.clear()
    if "uuid" not in request.session:
        request.session["uuid"] = str(uuid.uuid4())
    if "messages" not in request.session or not request.session["messages"]:
        request.session["messages"] = BASE_HISTORY
    return templates.TemplateResponse(
        "index.html", {"request": request, "messages": BASE_HISTORY}
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
        return markdown(response["output"])
        # return response["output"]
    except Exception as err:
        print(err)
        raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")


def init_agent(history):
    """Load an agent executor with tools and LLM"""
    tools = [
        Tool.from_function(
            name="find_similar_toys",
            func=find_similar_toys,
            description="""Useful when you need a toy recommendation. Returns
                           several toys that are related to the query. Only
                           recommend toys that are returned by this query. Input
                           should be a single string.""",
        ),
    ]
    llm = VertexAI(max_output_tokens=512, verbose=DEBUG)
    memory = ConversationBufferMemory(memory_key="chat_history")
    memory.load_memory_variables(history)
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=DEBUG,
        memory=memory,
        handle_parsing_errors=True,
    )
    agent.agent.llm_chain.verbose = DEBUG
    return agent


def find_similar_toys(desc: str) -> str:
    """Tool function for LangChain agent"""
    params = {"top_k": "5", "query": desc}

    response = requests.get(
        f"{BASE_URL}/semantic_similarity_search",
        params,
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )

    if response.status_code != 200:
        return f"Error trying to find similar toys: {response.text}"

    results = (
        [
            """Here are is list of toys related to the query in JSON format. Only
            use this list in making recommendations to the customer."""
        ]
        + [f"{r}" for r in response.json()]
    )
    if len(results) <= 1:
        return """There are no toys matching that query. Please try again or
                let the user know there are no results."""
    output = "\n".join(results)
    return output


def get_id_token():
    auth_req = google.auth.transport.requests.Request()
    target_audience = BASE_URL

    return google.oauth2.id_token.fetch_id_token(auth_req, target_audience)


if __name__ == "__main__":
    PORT = int(os.getenv("PORT")) if os.getenv("PORT") else 8080
    uvicorn.run(app, host="0.0.0.0", port=PORT)
