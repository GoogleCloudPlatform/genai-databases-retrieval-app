# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import asyncio
import os

import uvicorn

from app import init_app


async def main():
    PORT = int(os.getenv("PORT", default=8081))
    HOST = os.getenv("HOST", default="0.0.0.0")
    CLIENT_ID = os.getenv("CLIENT_ID")
    MIDDLEWARE_SECRET = os.getenv("MIDDLEWARE_SECRET", default="this is a secret")
    app = init_app(
        client_id=CLIENT_ID,
        middleware_secret=MIDDLEWARE_SECRET
    )
    if app is None:
        raise TypeError("app not instantiated")
    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=PORT, log_level="info"))
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
