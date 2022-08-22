import logging
from ..core import settings

# see: https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/#uvicorn-only-version


def setup_logging():
    logging.root.setLevel(settings.LOG_LEVEL)
    logging.getLogger("uvicorn.error").propagate = False
