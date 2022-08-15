from datetime import datetime, timedelta
import types
from uuid import uuid4
from devops_sccs.ats_cache import ats_cache

import pytest

# ----------------------------------------------------------------------------------------------------------------------
# Mock Bitbucket API resources
#
# Payloads follow the structures defined in the Bitbucket API
# https://developer.atlassian.com/cloud/bitbucket/rest/intro/
# See also pydantic models defined in devops_console_rest_api/models/*
#
# ----------------------------------------------------------------------------------------------------------------------
# Webhooks API payloads
# ----------------------------------------------------------------------------------------------------------------------

mock_user = {
    "is_staff": False,
    "account_id": "123",
}
mock_account = {
    "username": "test",
    "created_on": str(datetime.now() + timedelta(days=-365)),
    "uuid": uuid4().hex,
    "has_2fa_enabled": False,
}

mock_author = {
    "raw": "test",
    "user": mock_account,
}

mock_payloadworkspace = {
    "slug": "test",
    "name": "test",
    "uuid": uuid4().hex,
}

mock_payloadproject = {
    "name": "test",
    "uuid": uuid4().hex,
    "key": "test",
}

mock_payloadrepository = {
    "name": "test",
    "full_name": "test/test",
    "workspace": mock_payloadworkspace,
    "uuid": uuid4().hex,
    "project": mock_payloadproject,
    "website": "https://test.com",
    "scm": "git",
    "is_private": True,
}

mock_webhookevent = {
    "actor": mock_user,
    "repository": mock_payloadrepository,
}

mock_basecommit = {
    "type": "commit",
    "hash": "123456789",
    "date": datetime.now().__str__(),
    "author": mock_author,
    "summary": {},
}

mock_commitshort = {
    "type": "commit",
    "hash": "123456789",
    "message": "test",
    "author": mock_user,
    "links": {},
}

mock_referencestate = {
    "type": "branch",
    "name": "test",
    "target": mock_basecommit,
}

mock_pushchange = {
    "new": mock_referencestate,
    "old": {
        **mock_referencestate,
        "target": {
            **mock_basecommit,
            "date": str(datetime.now() + timedelta(days=-1)),
        },
    },
    "created": True,
    "forced": False,
    "closed": False,
    "commits": [mock_commitshort],
    "truncated": False,
}

mock_repopushevent = {
    **mock_webhookevent,
    "push": {
        "changes": [mock_pushchange],
    },
}


mock_repobuildstatuscreated = {}

mock_repobuildstatusupdated = {}

mock_prcreatedevent = {}

mock_prupdatedevent = {}

mock_prapprovedevent = {}

mock_prdeclinedevent = {}

mock_prmergedevent = {}

# ----------------------------------------------------------------------------------------------------------------------
# API payloads
# ----------------------------------------------------------------------------------------------------------------------

mock_project = {
    "key": "test",
}

mock_projectvalue = {
    "name": "test",
    "key": "test",
}

mock_configorprivilegevalue = {
    "short": "test",
    "key": "test",
}

mock_repositorypost = {
    "name": "test",
    "project": mock_projectvalue,
    "configuration": mock_configorprivilegevalue,
    "priviledges": mock_configorprivilegevalue,
}

mock_repositoryput = {
    **mock_repositorypost,
}

# ----------------------------------------------------------------------------------------------------------------------
# Mock Bitbucket Client
# ----------------------------------------------------------------------------------------------------------------------


@pytest.fixture
def mock_bitbucket_client(monkeypatch):
    from devops_console_rest_api.client import bitbucket_client

    @ats_cache()
    async def get_repository():
        return "mock success"

    monkeypatch.setattr(
        bitbucket_client, "get_repository", get_repository, raising=False
    )
    # raising=False to avoid raising an exception if the attr is not found
    # (which will be the case with our hacky runtime client)

    @ats_cache()
    async def get_repositories():
        return ["mock success"]

    monkeypatch.setattr(
        bitbucket_client, "get_repositories", get_repositories, raising=False
    )

    @ats_cache()
    async def add_repository():
        return "mock success"

    monkeypatch.setattr(
        bitbucket_client, "add_repository", add_repository, raising=False
    )

    @ats_cache()
    async def delete_repository():
        return "mock success"

    monkeypatch.setattr(
        bitbucket_client, "delete_repository", delete_repository, raising=False
    )

    @ats_cache()
    async def get_projects():
        return [mock_project]

    monkeypatch.setattr(bitbucket_client, "get_projects", get_projects, raising=False)

    @ats_cache()
    async def get_webhook_subscriptions():
        return "mock success"

    monkeypatch.setattr(
        bitbucket_client,
        "get_webhook_subscriptions",
        get_webhook_subscriptions,
        raising=False,
    )

    @ats_cache()
    async def create_webhook_subscription():
        return "mock success"

    monkeypatch.setattr(
        bitbucket_client,
        "create_webhook_subscription",
        create_webhook_subscription,
        raising=False,
    )

    @ats_cache()
    async def delete_webhook_subscription():
        return "mock success"

    monkeypatch.setattr(
        bitbucket_client,
        "delete_webhook_subscription",
        delete_webhook_subscription,
        raising=False,
    )

    monkeypatch.setattr(
        bitbucket_client, "cd_branches_accepted", ["test"], raising=False
    )
