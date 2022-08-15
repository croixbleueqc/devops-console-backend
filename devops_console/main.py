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


from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import router
from .api.v2.router import router as router_v2
from .core.config import settings
from .clients.client import CoreClient
from .webhooks_server.app import app as webhooks_server

# from .api.deps import azure_scheme

# initialize core
core = CoreClient()

app = FastAPI(
    # swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    # swagger_ui_init_oauth={
    #     "usePkceWithAuthorizationCodeGrant": True,
    #     "clientId": settings.OPENAPI_CLIENT_ID,
    # },
)


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# main API
app.include_router(router)
app.include_router(router_v2)

# webhook server mounted as a "subapp" to decouple it from the main API
app.mount(settings.WEBHOOKS_PATH, webhooks_server)


@app.exception_handler(HTTPException)
async def redirect_unauthorized(request: Request, exc):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # redirect to login page
        return RedirectResponse(url=f"{settings.API_V2_STR}/login")
    raise exc


@app.on_event("startup")
async def startup():
    for task in core.startup_tasks():
        await task()
    # load OpenID config
    # await azure_scheme.openid_config.load_config()


# shutdown
@app.on_event("shutdown")
async def shutdown():
    for task in core.shutdown_tasks():
        await task()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, port=5000)
