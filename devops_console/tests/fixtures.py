import logging
import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from devops_console import main
from devops_sccs.typing.credentials import Credentials

sccs_path = os.environ.get("API_V2_PATH", "/api/v2")
dev_token = os.environ.get("DEV_TOKEN", "superdupersecretdevtoken")

legacy_ws_path = "/wscom1"

user = os.environ.get("DEV_BB_USER")
author = os.environ.get("DEV_BB_AUTHOR")
apikey = os.environ.get("DEV_BB_APIKEY")
if user is None or author is None or apikey is None:
    logging.critical("Missing environment variables for devops-sccs")
    sys.exit(1)
dev_sccs_credentials = Credentials(user=user, author=author, apikey=apikey)

test_headers = {"Authorization": f"Bearer {dev_token}"}


class TestCore:
    """Initialize a test instance and provide references to useful runtime objects."""

    __instance = None

    def __new__(cls):
        # Singleton pattern
        if cls.__instance is None:
            cls.__instance = super(TestCore, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        self.testcore = main.core
        with TestClient(main.app) as testclient:
            self.testclient = testclient


# glabal testcore instance
testcore = TestCore()

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
