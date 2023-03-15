import logging
import sys

from loguru import logger

from devops_console.core import settings


# see: https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/#uvicorn-only-version


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    # intercept everything at the root logger level
    logging.root.handlers = [InterceptHandler()]
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    logging.root.setLevel(log_level)

    # remove every other logger's handlers
    # and propagate to the root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # configure loguru
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": False}])
