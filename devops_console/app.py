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

# from devops_console_rest_api import main as rest_api_main

from fastapi import FastAPI

from devops_console.core.core import Core

from .api.v1.router import router
from .config import Config
from .core import get_core

core: Core


class App:
    def __init__(self, config: Config | None = None):
        # Config
        if config is None:
            config = Config()
        self.config = config

        global core
        core = get_core(config=config)

        # Application
        app = FastAPI()

        # Create and share the core for all APIs
        app.include_router(router)

        # Create and share websockets

        # Set background tasks (startup)
        @app.on_event("startup")
        async def startup():
            for task in get_core().startup_tasks():
                await task()

        # shutdown
        @app.on_event("shutdown")
        async def shutdown():
            for task in get_core().shutdown_tasks():
                await task()

        self.app = app
