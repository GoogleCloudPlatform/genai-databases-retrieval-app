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
from datetime import datetime
from typing import Any,Dict, Optional

import aiohttp
import google.auth
import google.oauth2.id_token  # type: ignore
from google.auth.credentials import TokenState
from google.auth import compute_engine  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from langchain.agents.agent import ExceptionTool  # type: ignore
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field

BASE_URL = os.getenv("BASE_URL", default="http://localhost:8080")
CREDENTIALS = None


def filter_none_values(params: dict) -> dict:
    return {key: value for key, value in params.items() if value is not None}


def get_id_token():
    global CREDENTIALS
    if CREDENTIALS is None:
        CREDENTIALS, _ = google.auth.default()
        if not hasattr(CREDENTIALS, "id_token"):
            # Use Compute Engine default credential
            CREDENTIALS = compute_engine.IDTokenCredentials(
                request=Request(),
                target_audience=BASE_URL,
                use_metadata_identity_endpoint=True,
            )
    if not CREDENTIALS.valid:
        CREDENTIALS.refresh(Request())
    if hasattr(CREDENTIALS, "id_token"):
        return CREDENTIALS.id_token
    else:
        return CREDENTIALS.token


def add_auth_header():
    """Helper method to generate ID tokens for authenticated requests"""
    # Append ID Token to make authenticated requests to Cloud Run services
    return f"Bearer {get_id_token()}"

def get_confirmation_needing_tools():
    return ["Insert Ticket"]
