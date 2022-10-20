# Copyright 2019 mickybart
# Copyright 2020 Croix Bleue du Québec

# This file is part of devops-console-backend.

# devops-console-backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# devops-console-backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with devops-console-backend.  If not, see <https://www.gnu.org/licenses/>.


from functools import reduce
import secrets
import os
import sys

from pathlib import Path
from pydantic import AnyHttpUrl, BaseSettings, Field
from loguru import logger

from ..schemas.userconfig import UserConfig
from ..schemas.webhooks import WebhookEventKey
from ..utils.helpers import deep_replace, read_json_file


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    BRANCH_NAME: str = Field(default="undefined", env="BRANCH_NAME")

    HOST: AnyHttpUrl = Field(default="http://localhost:5000", env="HOST")

    API_V1_STR = ""
    API_V2_STR = "/api/v2"

    AUTH_PATH: str = Field(default="/token", env="AUTH_PATH")

    WEBHOOKS_HOST: str = Field(default="localhost:4242", env="WEBHOOKS_HOST")
    WEBHOOKS_PATH: str = Field(default="/bitbucketcloud/hooks/repo", env="WEBHOOKS_PATH")

    WEBHOOKS_DEFAULT_EVENTS = (
        WebhookEventKey.repo_push,
        WebhookEventKey.repo_build_created,
        WebhookEventKey.repo_build_updated,
        WebhookEventKey.pr_created,
        WebhookEventKey.pr_updated,
        WebhookEventKey.pr_approved,
        WebhookEventKey.pr_declined,
        WebhookEventKey.pr_merged,
    )

    WEBHOOKS_DEFAULT_DESCRIPTION = "Default webhook created via DevOps Console"

    DATABASE_URI: str = Field(default="sqlite://", env="DATABASE_URI")

    SECRET_KEY: str = Field(default=secrets.token_urlsafe(32), env="SECRET_KEY")
    ACCESS_TOKEN_TTL: int = Field(default=60 * 24 * 7, env="ACCESS_TOKEN_TTL")
    ALGORITHM = "HS256"
    # used to authenticate as admin in tests and dev
    DEV_AUTH: bool = Field(default=False, env="DEV_AUTH")
    DEV_TOKEN: str = Field(default="superdupersecretdevtoken", env="DEV_TOKEN")

    # TODO: Finish azure auth config
    APP_CLIENT_ID: str = Field(default="", env="APP_CLIENT_ID")
    TENANT_ID: str = Field(default="", env="TENANT_ID")
    OPENAPI_CLIENT_ID: str = Field(default="", env="OPENAPI_CLIENT_ID")
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = [
        "http://localhost:8080",
        ]

    userconfig: UserConfig

    class Config:
        env_file = ".env"
        case_sensitive = True

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                userconfig_src,
                env_settings,
                file_secret_settings,
            )


def userconfig_src(settings: BaseSettings):
    """Reads from JSON files found in the "config" directory."""

    env = os.environ.get("BRANCH_NAME", "undefined")

    dirpath = Path.cwd() / "config"

    default_json = dirpath.joinpath("default.json")
    env_json = dirpath.joinpath(env + ".json")
    local_json = dirpath.joinpath("local.json")

    if all(not f.exists() for f in [default_json, env_json, local_json]):
        logger.critical("No config files found, exiting")
        sys.exit(1)

    (default_dict, env_dict, local_json_dict) = map(
        read_json_file, [default_json, env_json, local_json]
    )

    # Order is important inside the list (last one is the most important)
    dicts = list(filter(lambda x: x != {}, [default_dict, env_dict, local_json_dict]))
    merged: dict = reduce(lambda a, b: a | b, dicts)

    # replace all 'env' with BRANCH_NAME
    configs = deep_replace(merged, env=env)

    userconfig = UserConfig.parse_obj(configs)

    return {"userconfig": userconfig}
