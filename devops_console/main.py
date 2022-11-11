# Copyright 2019 mickybart
# Copyright 2020 Croix Bleue du Québec

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import router
from .api.v2.router import main_router as router_v2
from .clients.client import CoreClient
# from .api.deps import azure_scheme
from .core import settings
from .utils.logs import setup_logging
from .webhooks_server.app import app as webhooks_server

setup_logging()
# initialize core
core = CoreClient()

app = FastAPI()

if settings.BACKEND_CORS_ORIGINS is not None and len(settings.BACKEND_CORS_ORIGINS) > 0:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        )
    logging.debug("Added CORS middleware")

# main API
logging.debug("Adding API routes")
app.include_router(router)
app.include_router(router_v2)

# webhook server mounted as a "subapp" to decouple it from the main API
app.mount(settings.WEBHOOKS_PATH, webhooks_server)
logging.debug(f"Webhooks server mounted on {settings.WEBHOOKS_PATH} endpoint")


# @app.exception_handler(HTTPException)
# async def redirect_unauthorized(request: Request, exc):
#     if exc.status_code == status.HTTP_401_UNAUTHORIZED:
#         # redirect to login page
#         return RedirectResponse(url="/login")
#     raise exc


@app.on_event("startup")
async def startup():
    logging.debug("Running startup tasks")
    for task in core.startup_tasks():
        await task()
    # load OpenID config
    # await azure_scheme.openid_config.load_config()


# shutdown
@app.on_event("shutdown")
async def shutdown():
    logging.debug("Running shutdown tasks")
    for task in core.shutdown_tasks():
        await task()


if __name__ == "__main__":
    import uvicorn

    server = uvicorn.Server(
        uvicorn.Config(
            "devops_console.main:app",
            host="0.0.0.0",
            port=5000,
            )
        )

    uvicorn.run("main:app", reload=True, port=5000)
