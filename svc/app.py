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

from aiohttp import web
from aiohttp.web_log import AccessLogger
from aiohttp_swagger import setup_swagger

import logging
import os

from .config import Config
from .core import getCore
from . import apiv1
from . import monitoring

class FilterAccessLogger(AccessLogger):
    """/health and /metrics filter

    Hidding those requests if we have a 200 OK when we are not in DEBUG
    """
    def log(self, request, response, time):
        if self.logger.level != logging.DEBUG \
            and response.status == 200 \
            and request.path in ['/health','/metrics']:

            return

        super().log(request, response, time)

class App:
    def __init__(self):
        # Config
        config = Config()

        # Logging
        logging_default_format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

        gunicorn_error = logging.getLogger("gunicorn.error")
        if len(gunicorn_error.handlers) != 0:
            # Seems to use gunicorn so we are using the provided logging level
            logging_level = gunicorn_error.level
        else:
            # using LOGGING_LEVEL env or fallback to DEBUG
            logging_level = int(os.environ.get("LOGGING_LEVEL", logging.DEBUG))

        logging.basicConfig(
            level=logging_level,
            format=logging_default_format
        )

        aiohttp_access = logging.getLogger("aiohttp.access")
        aiohttp_access.setLevel(logging_level)

        # Application
        self.app = web.Application(
            handler_args={
                'access_log_class': FilterAccessLogger
            }
        )
        apiv1.setup(self.app)
        monitoring.setup(self.app)

        if config["api"]["swagger"]["url"] is not None:
            setup_swagger(
                self.app,
                title=config["api"]["title"],
                api_version=config["api"]["version"],
                description=config["api"]["description"],
                swagger_url=config["api"]["swagger"]["url"]
            )

        # Create and share the core for all APIs
        self.app["core"] = getCore(config=config)

        # Set background tasks (startup)
        for background_task in getCore().startup_background_tasks():
            self.app.on_startup.append(background_task)

        # Set background tasks (cleanup)
        for background_task in getCore().cleanup_background_tasks():
            self.app.on_cleanup.append(background_task)

    def run(self):
        web.run_app(self.app, host="0.0.0.0", port=5000)
