from aiohttp.web import Application

from ...wscom import wscom_setup
from . import health, kubernetes, oauth2, sccs, wscom1


def setup(app: Application) -> None:
    app.add_routes(health.routes)

    app.add_routes(wscom1.routes)

    wscom_setup(app, wscom1.DISPATCHERS_APP_KEY, "sccs", sccs.wscom_dispatcher)

    wscom_setup(app, wscom1.DISPATCHERS_APP_KEY, "k8s", kubernetes.wscom_dispatcher)

    wscom_setup(app, wscom1.DISPATCHERS_APP_KEY, "oauth2", oauth2.wscom_dispatcher)
