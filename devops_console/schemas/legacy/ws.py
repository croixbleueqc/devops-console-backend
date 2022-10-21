from __future__ import annotations

import json
from dataclasses import dataclass

from devops_sccs.typing.credentials import Credentials


@dataclass
class WsRequest:
    deeplink: str
    action: str
    path: str

    def __str__(self) -> str:
        return f"{self.deeplink}:{self.action}:{self.path}"

    @classmethod
    def from_str(cls, request: str) -> WsRequest:
        deeplink, action, path = request.split(":")
        return cls(deeplink, action, path)


@dataclass
class WsSession:
    team: str
    user: str
    apikey: str
    author: str

    @classmethod
    def from_credentials(cls, credentials: Credentials) -> WsSession:
        return cls(
            team="croixbleue",
            user=credentials.user,
            apikey=credentials.apikey,
            author=credentials.author,
            )

    def dict(self) -> dict:
        return {
            "team": self.team,
            "user": self.user,
            "apikey": self.apikey,
            "author": self.author,
            }


@dataclass
class WsDataRequest:
    plugin_id: str
    session: WsSession
    repository: str | None = None
    environment: str | None = None
    environments: list[str] | None = None
    version: str | None = None
    args: dict | None = None

    def dict(self) -> dict:
        return {
            "plugin": self.plugin_id,
            "session": self.session.dict(),
            "repository": self.repository,
            "environment": self.environment,
            "environments": self.environments,
            "version": self.version,
            "args": self.args,
            }


@dataclass
class WsMessage:
    unique_id: str
    request: WsRequest
    data_request: WsDataRequest | None = None
    error: str | None = None

    def dumps(self) -> str:
        return json.dumps(
            {
                "uniqueId": self.unique_id,
                "request": str(self.request),
                "dataRequest": self.data_request.dict() if self.data_request else None,
                }
            )

    def dict(self) -> dict:
        return {
            "uniqueId": self.unique_id,
            "request": str(self.request),
            "dataRequest": self.data_request.dict() if self.data_request else None,
            }


@dataclass
class WsResponse:
    unique_id: str
    data_response: dict | None
    error: str | None = None

    def dumps(self) -> str:
        if self.data_response is not None:
            return json.dumps(
                {
                    "uniqueId": self.unique_id,
                    "dataResponse": self.data_response,
                    }
                )
        elif self.error is not None:
            return json.dumps(
                {
                    "uniqueId": self.unique_id,
                    "error": self.error,
                    }
                )

        raise ValueError("No dataResponse or error in response")

    def json(self) -> dict:
        return {"uniqueId": self.unique_id, "dataResponse": self.data_response, "error": self.error}

    @classmethod
    def from_json(cls, data: dict) -> WsResponse:
        return cls(
            data["uniqueId"],
            data.get("dataResponse", None),
            data.get("error", None),
            )
