import json
from http import HTTPStatus

from fastapi.testclient import TestClient

from devops_console.main import app
from .fixtures import sccs_path, test_headers


def test_get_repos():
    with TestClient(app) as client:
        response = client.get(sccs_path + "/sccs/repositories", headers=test_headers)
        assert response.status_code == HTTPStatus.OK


def test_not_authorized():
    with TestClient(app) as client:
        response = client.get(sccs_path + "/repositories")
        assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_repository_by_uuid():
    with TestClient(app) as client:
        existingrepouuid = "{db7f9529-2ab4-4d80-8321-0b6a215402b7}"  # aiobitbucket-wip
        response = client.get(sccs_path + f"/repositories/{existingrepouuid}", headers=test_headers)
        assert response.status_code == HTTPStatus.OK


def test_get_repository_by_uuid_not_found():
    with TestClient(app) as client:
        nonexistingrepouuid = "{f8f8f8f8-f8f8-f8f8-f8f8-f8f8f8f8f8f8}"
        response = client.get(
            sccs_path + f"/repositories/{nonexistingrepouuid}", headers=test_headers
            )
        assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_repository_by_name():
    with TestClient(app) as client:
        existingrepo = "aiobitbucket-wip"
        response = client.get(sccs_path + f"/repositories/{existingrepo}", headers=test_headers)
        assert response.status_code == HTTPStatus.OK


def test_get_repository_by_name_not_found():
    with TestClient(app) as client:
        response = client.get(sccs_path + "/repositories/nonexisting", headers=test_headers)
        assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_repo():
    with TestClient(app) as client:
        pass
        # TODO: implement a safe version of this test and other write tests
        # response = client.post(
        #     sccs_path + "/repositories",
        #     headers=test_headers,
        #     data=json.dumps(mock_repositorypost),
        # )
        # assert response.status_code == HTTPStatus.OK


def test_create_repo_invalid_payload():
    with TestClient(app) as client:
        response = client.post(
            sccs_path + "/repositories", headers=test_headers, data=json.dumps({})
            )
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_repo():
    with TestClient(app) as client:
        pass
        # response = client.put(
        #     sccs_path + "/repositories/test", data=json.dumps(mock_repositoryput)
        # )
        # assert response.status_code == HTTPStatus.OK


def test_update_repo_invalid_payload():
    with TestClient(app) as client:
        response = client.put(
            sccs_path + "/repositories/test", headers=test_headers, data=json.dumps({})
            )
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_repo():
    with TestClient(app) as client:
        pass
        # response = client.delete(sccs_path + "/repositories/test")
        # assert response.status_code == HTTPStatus.OK


def test_delete_repo_not_found():
    with TestClient(app) as client:
        response = client.delete(sccs_path + "/repositories/nonexisting", headers=test_headers)
        assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_webhook_subscriptions():
    with TestClient(app) as client:
        response = client.get(sccs_path + "/repositories/webhooks", headers=test_headers)
        assert response.status_code == HTTPStatus.OK


def test_create_default_webhooks():
    with TestClient(app) as client:
        pass
        # response = client.get(sccs_path + "/repositories/create_default_webhooks")
        # assert response.status_code == HTTPStatus.OK


def test_remove_default_webhooks():
    with TestClient(app) as client:
        pass
        # response = client.get(sccs_path + "/repositories/remove_default_webhooks")
        # assert response.status_code == HTTPStatus.OK


def test_get_projects():
    with TestClient(app) as client:
        response = client.get(sccs_path + "/projects", headers=test_headers)
        assert response.status_code == HTTPStatus.OK
