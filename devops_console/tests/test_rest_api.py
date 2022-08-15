from http import HTTPStatus
import json
from devops_console_rest_api.api.v1.endpoints.bitbucket import router
from devops_console_rest_api.config import API_V1_STR
from fastapi import FastAPI
from fastapi.testclient import TestClient
from .fixtures import mock_bitbucket_client, mock_repositorypost, mock_repositoryput

app = FastAPI()

bb_endpoint = API_V1_STR + "/bb"  # same as the real api

app.include_router(router, prefix=bb_endpoint)

client = TestClient(app)


def test_get_repos(mock_bitbucket_client):
    response = client.get(bb_endpoint + "/repos")
    assert response.status_code == HTTPStatus.OK


def test_get_repository_by_name(mock_bitbucket_client):
    response = client.get(bb_endpoint + "/repos/test")
    assert response.status_code == HTTPStatus.OK


def test_get_repository_by_uuid(mock_bitbucket_client):
    response = client.get(bb_endpoint + "/repos/uuid")
    assert response.status_code == HTTPStatus.OK


def test_get_repository_by_name_not_found(mock_bitbucket_client):
    response = client.get(bb_endpoint + "/repos/nonexisting")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_repo(mock_bitbucket_client):
    response = client.post(bb_endpoint + "/repos", data=json.dumps(mock_repositorypost))
    assert response.status_code == HTTPStatus.OK


def test_create_repo_invalid_payload(mock_bitbucket_client):
    response = client.post(bb_endpoint + "/repos", data=json.dumps({}))
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_repo(mock_bitbucket_client):
    response = client.put(
        bb_endpoint + "/repos/test", data=json.dumps(mock_repositoryput)
    )
    assert response.status_code == HTTPStatus.OK


def test_update_repo_invalid_payload(mock_bitbucket_client):
    response = client.put(bb_endpoint + "/repos/test", data=json.dumps({}))
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_repo(mock_bitbucket_client):
    response = client.delete(bb_endpoint + "/repos/test")
    assert response.status_code == HTTPStatus.OK


def test_delete_repo_not_found(mock_bitbucket_client):
    response = client.delete(bb_endpoint + "/repos/nonexisting")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_webhook_subscriptions(mock_bitbucket_client):
    response = client.get(bb_endpoint + "/repos/webhooks")
    assert response.status_code == HTTPStatus.OK


def test_create_default_webhooks(mock_bitbucket_client):
    response = client.get(bb_endpoint + "/repos/create_default_webhooks")
    assert response.status_code == HTTPStatus.OK


def test_remove_default_webhooks(mock_bitbucket_client):
    response = client.get(bb_endpoint + "/repos/remove_default_webhooks")
    assert response.status_code == HTTPStatus.OK


def test_get_projects(mock_bitbucket_client):
    response = client.get(bb_endpoint + "/projects")
    assert response.status_code == HTTPStatus.OK
