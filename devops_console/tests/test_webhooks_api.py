import json
from http import HTTPStatus

from fastapi.testclient import TestClient

from devops_console.main import app
from devops_console.schemas import WebhookEventKey
from .fixtures import mock_repopushevent


def test_handle_webhook_event_invalid_body():
    with TestClient(app) as client:
        response = client.post(
            "/",
            headers={"X-Event-Key": WebhookEventKey.repo_push.value},
            data="[]",
            )
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_handle_webhook_event_invalid_header():
    with TestClient(app) as client:
        response = client.post("/", headers={"X-Event-Key": "gibberish"}, data="{}")
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_handle_webhook_event_repo_push():
    with TestClient(app) as client:
        response = client.post(
            "/",
            headers={"X-Event-Key": WebhookEventKey.repo_push.value},
            data=json.dumps(mock_repopushevent),
            )

        assert response.status_code == HTTPStatus.OK


def test_handle_webhook_event_repo_build_created():
    # TODO: implement
    pass


def test_handle_webhook_event_repo_build_updated():
    # TODO: implement
    pass


def test_handle_webhook_event_pr_created():
    # TODO: implement
    pass


def test_handle_webhook_event_pr_updated():
    # TODO: implement
    pass


def test_handle_webhook_event_pr_approved():
    # TODO: implement
    pass


def test_handle_webhook_event_pr_declined():
    # TODO: implement
    pass


def test_handle_webhook_event_pr_merged():
    # TODO: implement
    pass
