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

from devops_sccs.client import SccsClient
from devops_sccs.schemas.config import SccsConfig


def ctx_wrap(wrapped):
    async def _wrapper(self, plugin_id, credentials, *args, **kwargs):
        async with self.core.context(plugin_id, credentials) as ctx:
            method = getattr(ctx, wrapped.__name__)
            return await method(*args, **kwargs)

    return _wrapper


def ctx_wrap_generator(wrapped):
    async def _wrapper(self, plugin_id, credentials, *args, **kwargs):
        async with self.core.context(plugin_id, credentials) as ctx:
            method = getattr(ctx, wrapped.__name__)
            async for item in await method(*args, **kwargs):
                yield item

    return _wrapper


class Sccs:
    """Responsible for encapsulating the client's methods in a context manager"""
    _instance = None
    cd_branches_accepted: list[str]
    core: SccsClient
    config: SccsConfig

    def __new__(cls, config: SccsConfig):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls.config = config
        return cls._instance

    async def init(self) -> None:
        self.core = await SccsClient.create(self.config)

    def context(self, plugin_id, args):
        return self.core.context(plugin_id, args)

    @ctx_wrap
    async def get_repository(self, plugin_id, credentials, repo_name, *args, **kwargs):
        pass

    @ctx_wrap
    async def get_repository_permission(self, plugin_id, credentials, *args, **kwargs):
        pass

    @ctx_wrap
    async def get_repositories(self, plugin_id, credentials, *args, **kwargs):
        pass

    @ctx_wrap
    async def passthrough(self, plugin_id, credentials, request, *args, **kwargs):
        pass

    @ctx_wrap
    async def get_continuous_deployment_config(
            self, plugin_id, credentials, repo_name, environments=None, *args, **kwargs
            ):
        pass

    @ctx_wrap
    async def trigger_continuous_deployment(
            self, plugin_id, credentials, repo_name, environment, version
            ):
        pass

    @ctx_wrap
    async def get_continuous_deployment_environments_available(
            self, plugin_id, credentials, repo_name
            ):
        pass

    @ctx_wrap
    async def get_continuous_deployment_versions_available(
            self, plugin_id, credentials, repo_name, *args, **kwargs
            ):
        pass

    @ctx_wrap
    async def bridge_repository_to_namespace(
            self, plugin_id, credentials, repository, environment, untrustable=True, *args, **kwargs
            ):
        pass

    @ctx_wrap
    async def get_add_repository_contract(self, plugin_id, credentials):
        pass

    @ctx_wrap
    async def add_repository(
            self, plugin_id, credentials, repository, template, template_params, *args, **kwargs
            ):
        pass

    @ctx_wrap
    async def delete_repository(self, plugin_id, credentials, repo_name):
        pass

    @ctx_wrap
    async def compliance_report(self, plugin_id, credentials, *args, **kwargs):
        pass

    @ctx_wrap
    async def get_webhook_subscriptions(
            self,
            plugin_id,
            credentials,
            repo_name: str,
            *args,
            **kwargs
            ):
        pass

    @ctx_wrap
    async def create_webhook_subscription(self, plugin_id, credentials, *args, **kwargs):
        pass

    @ctx_wrap
    async def delete_webhook_subscription(self, plugin_id, credentials, *args, **kwargs):
        pass

    @ctx_wrap
    async def get_projects(self, plugin_id, credentials):
        pass

    @ctx_wrap
    async def watch_repositories(
            self,
            plugin_id,
            credentials,
            poll_interval,
            send_stream,
            ):
        pass

    @ctx_wrap
    async def watch_continuous_deployment_config(
            self,
            plugin_id,
            credentials,
            poll_interval,
            send_stream,
            repo_name,
            environments,
            ):
        pass

    @ctx_wrap
    async def watch_continuous_deployment_versions_available(
            self, plugin_id, credentials, poll_interval, send_stream, repo_name
            ):
        pass

    @ctx_wrap
    async def watch_continuous_deployment_environments_available(
            self, plugin_id, credentials, poll_interval, send_stream, repo_name,
            ):
        pass
