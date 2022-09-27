import pytest

from .fixtures import dev_sccs_credentials, legacy_ws_path, testcore
from devops_console.schemas.legacy.ws import WsDataRequest, WsMessage, WsRequest, WsSession

testclient = testcore.testclient


def test_ws_connect():
    with testclient.websocket_connect(legacy_ws_path) as ws:
        assert ws is not None


def test_ws_watch_repositories():
    uid = "123"
    request = WsRequest("sccs", "watch", "/repositories")
    data_request = WsDataRequest(
        plugin_id="cbq",
        session=WsSession.from_credentials(dev_sccs_credentials),
    )
    msg = WsMessage(unique_id=uid, request=request, data_request=data_request)
    with testclient.websocket_connect(legacy_ws_path) as ws:
        ws.send_json(msg.dict())
        response = ws.receive_json()

        assert response["uniqueId"] == uid
        assert response["dataResponse"] is not None
        with pytest.raises(KeyError):
            assert response["dataResponse"]["error"]
        # TODO add more assertions


def test_ws_watch_continuous_deployment_config():
    uid = "1234"
    request = WsRequest("sccs", "watch", "/repository/cd/config")
    data_request = WsDataRequest(
        plugin_id="cbq",
        session=WsSession.from_credentials(dev_sccs_credentials),
        repository="aiobitbucket-wip",
    )
    msg = WsMessage(unique_id=uid, request=request, data_request=data_request)
    with testclient.websocket_connect(legacy_ws_path) as ws:
        ws.send_json(msg.dict())
        response = ws.receive_json()

        assert response["uniqueId"] == uid
        assert response["dataResponse"] is not None
        with pytest.raises(KeyError):
            assert response["dataResponse"]["error"]
        # TODO add more assertions


def test_ws_watch_continuous_deployment_versions_available():
    uid = "12345"
    request = WsRequest("sccs", "watch", "/repository/cd/versions_available")
    data_request = WsDataRequest(
        plugin_id="cbq",
        session=WsSession.from_credentials(dev_sccs_credentials),
        repository="aiobitbucket-wip",
    )
    msg = WsMessage(unique_id=uid, request=request, data_request=data_request)
    with testclient.websocket_connect(legacy_ws_path) as ws:
        ws.send_json(msg.dict())
        response = ws.receive_json()

        assert response["uniqueId"] == uid
        assert response["dataResponse"] is not None
        with pytest.raises(KeyError):
            assert response["dataResponse"]["error"]
        # TODO add more assertions


def test_ws_watch_continuous_deployment_environments_available():
    uid = "123456"
    request = WsRequest("sccs", "watch", "/repository/cd/environments_available")
    data_request = WsDataRequest(
        plugin_id="cbq",
        session=WsSession.from_credentials(dev_sccs_credentials),
        repository="aiobitbucket-wip",
    )
    msg = WsMessage(unique_id=uid, request=request, data_request=data_request)
    with testclient.websocket_connect(legacy_ws_path) as ws:
        ws.send_json(msg.dict())
        response = ws.receive_json()

        assert response["uniqueId"] == uid
        assert response["dataResponse"] is not None
        with pytest.raises(KeyError):
            assert response["dataResponse"]["error"]
        # TODO add more assertions
