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

import asyncio
import threading

from aiohttp import web, WSCloseCode
from aiohttp.web_log import AccessLogger
from aiohttp_swagger import setup_swagger
from devops_console_rest_api import main as rest_api_main

import logging
import os
import weakref

from .config import Config
from .core import getCore
from .api import v1 as api
from . import monitoring


def _start_background_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()
    loop.close()


_LOOP = asyncio.new_event_loop()
_LOOP_THREAD = threading.Thread(
    target=_start_background_loop, args=(_LOOP,), daemon=True
)
_LOOP_THREAD.start()


class FilterAccessLogger(AccessLogger):
    """/health and /metrics filter

    Hidding those requests if we have a 200 OK when we are not in DEBUG
    """

    def log(self, request, response, time):
        if (
            self.logger.level != logging.DEBUG
            and response.status == 200
            and request.path in ["/health", "/metrics"]
        ):

            return

        super().log(request, response, time)


class App:
    def __init__(self, config: Config | None = None):
        # Config
        if config is None:
            config = Config()
        self.config = config

        # Logging
        logging_default_format = (
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )

        gunicorn_error = logging.getLogger("gunicorn.error")
        if len(gunicorn_error.handlers) != 0:
            # Seems to use gunicorn so we are using the provided logging level
            logging_level = gunicorn_error.level
        else:
            # using LOGGING_LEVEL env or fallback to DEBUG
            logging_level = int(os.environ.get("LOGGING_LEVEL", logging.DEBUG))

        logging.basicConfig(level=logging_level, format=logging_default_format)

        aiohttp_access = logging.getLogger("aiohttp.access")
        aiohttp_access.setLevel(logging_level)

        # Application
        self.app = web.Application(
            handler_args={"access_log_class": FilterAccessLogger}
        )

        api.setup(self.app)
        monitoring.setup(self.app)

        if config["api"]["swagger"]["url"] is not None:
            setup_swagger(
                self.app,
                title=config["api"]["title"],
                api_version=config["api"]["version"],
                description=config["api"]["description"],
                swagger_url=config["api"]["swagger"]["url"],
                ui_version=3,
            )

        # Create and share the core for all APIs
        core = getCore(config=config)

        self.app["core"] = core

        # Create and share websockets
        self.app["websockets"] = weakref.WeakSet()

        # Set background tasks (startup)
        for background_task in getCore().startup_background_tasks():
            self.app.on_startup.append(background_task)

        # shutdown
        self.app.on_shutdown.append(on_shutdown)

        # Set background tasks (cleanup)
        for background_task in getCore().cleanup_background_tasks():
            self.app.on_cleanup.append(background_task)

        # Start subserver
        self.start_subserver(core.sccs)

    def run(self):
        web.run_app(self.app, host="0.0.0.0", port=5000, loop=_LOOP)

    def start_subserver(self, sccs) -> None:
        """Start the FastAPI subserver in a separate thread"""

        # we need to pass a reference of the event loop to the subserver
        # so that we can make calls from it to the sccs plugin in this thread
        def run(loop) -> None:
            rest_api_main.run(
                cfg=self.config,
                core_sccs=sccs,
                loop=_LOOP,
            )

        thread = threading.Thread(
            target=run,
            args=(asyncio.new_event_loop(),),
            name="FastAPI subserver",
            daemon=True,
        )
        thread.start()


async def on_shutdown(app: web.Application):
    for ws in set(app["websockets"]):
        await ws.close(code=WSCloseCode.GOING_AWAY, message="Server shutdown")

    # app["rest_api"].join()
