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

import logging

from devops_sccs.client import SccsClient

from ..schemas.userconfig import SCCSConfig


class Sccs:
    """Sccs Core"""

    cd_branches_accepted: list[str]

    def __init__(self, config: SCCSConfig):
        self.config = config
        self.core: SccsClient

    async def init(self) -> None:
        self.core = await SccsClient.create(self.config.dict())
        """ TODO: propagate models so that we can use them directly rather
        than having to "dict()" them """

    def context(self, plugin_id, args):
        return self.core.context(plugin_id, args)

    async def get_repository(self, plugin_id, session, *args, **kwargs):
        try:
            async with self.core.context(plugin_id, session) as ctx:
                return await ctx.get_repository(*args, **kwargs)
        except:
            logging.exception("Failed to get repository")
            raise

    async def get_repositories(self, plugin_id, session, *args, **kwargs) -> list:
        try:
            async with self.core.context(plugin_id, session) as ctx:
                return await ctx.get_repositories(*args, **kwargs)
        except:
            logging.exception("get repositories")
            raise

    async def watch_repositories(self, plugin_id, session, *args, **kwargs):
        async with self.core.context(plugin_id, session) as ctx:
            async for event in await ctx.watch_repositories(*args, **kwargs):
                yield event

    async def passthrough(self, plugin_id, session, request, args):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.passthrough(request, args)

    async def get_continuous_deployment_config(
        self, plugin_id, session, repository, environments=None, args=None
    ):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.get_continuous_deployment_config(
                repository=repository, environments=environments, args=args
            )

    async def watch_continuous_deployment_config(
        self, plugin_id, session, repository, environments, args
    ):
        async with self.core.context(plugin_id, session) as ctx:
            async for event in await ctx.watch_continuous_deployment_config(
                repository, environments, args=args
            ):
                yield event

    async def watch_continuous_deployment_versions_available(
        self, plugin_id, session, repository, args
    ):
        async with self.core.context(plugin_id, session) as ctx:
            async for event in await ctx.watch_continuous_deployment_versions_available(
                repository, args=args
            ):
                yield event

    async def trigger_continuous_deployment(
        self, plugin_id, session, repository, environment, version, args
    ):
        try:
            async with self.core.context(plugin_id, session) as ctx:
                return await ctx.trigger_continuous_deployment(
                    repository, environment, version, args
                )
        except:
            logging.exception("trigger_continuous_deployment")
            raise

    async def get_continuous_deployment_environments_available(
        self, plugin_id, session, repository, args
    ):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.get_continuous_deployment_environments_available(
                repository, args
            )

    async def watch_continuous_deployment_environments_available(
        self, plugin_id, session, repository, args
    ):
        async with self.core.context(plugin_id, session) as ctx:
            async for event in await ctx.watch_continuous_deployment_environments_available(
                repository, args=args
            ):
                yield event

    async def get_continuous_deployment_versions_available(
        self, plugin_id, session, repository, args=None
    ):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.get_continuous_deployment_versions_available(
                repository, args
            )

    async def bridge_repository_to_namespace(
        self, plugin_id, session, repository, environment, untrustable=True, args=None
    ):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.bridge_repository_to_namespace(repository, environment)

    async def get_add_repository_contract(self, plugin_id, session):
        async with self.core.context(plugin_id, session) as ctx:
            return ctx.get_add_repository_contract()

    async def add_repository(
        self, plugin_id, session, repository, template, template_params, args
    ):
        try:
            async with self.core.context(plugin_id, session) as ctx:
                return await ctx.add_repository(
                    repository, template, template_params, args
                )
        except:
            logging.exception("add repository")
            raise

    async def delete_repository(self, plugin_id, session, repo_name):
        try:
            async with self.core.context(plugin_id, session) as ctx:
                return await ctx.delete_repository(repo_name)
        except:
            logging.exception("delete repository")
            raise

    async def compliance_report(self, plugin_id, session, args):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.compliance_report(args)

    async def get_webhook_subscriptions(self, plugin_id, session, **kwargs) -> dict:
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.get_webhook_subscriptions(**kwargs)

    async def create_webhook_subscription(self, plugin_id, session, **kwargs):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.create_webhook_subscription(**kwargs)

    async def delete_webhook_subscription(self, plugin_id, session, **kwargs):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.delete_webhook_subscription(**kwargs)

    async def get_projects(self, plugin_id, session):
        async with self.core.context(plugin_id, session) as ctx:
            return await ctx.get_projects()
