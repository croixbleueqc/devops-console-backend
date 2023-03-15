import os
from pathlib import Path

import pygit2
from anyio import sleep
from kubernetes_asyncio.client.api_client import json
from loguru import logger

from devops_console.sccs.errors import SccsException
from devops_console.models.config.sccs_config import SccsPluginConfig, VaultConfig
from devops_console.utils.storage_helpers import get_superuser

from .provision import GitCredentials
from .storage_models import (
    BranchRestriction,
    Privileges,
    RepositoryConfiguration,
    Restriction,
    SshKey,
    StorageDefinition,
)


class ManagementStorage:
    """Fetches storage configurations from our upstream management repo:
    https://bitbucket.org/croixbleue/bitbucket-management-storage/src/master/
    and stores them *on disk*
    """

    _instance = None
    config_repository = None
    config_origin = None

    def __new__(cls, *args):
        # Singleton
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: SccsPluginConfig) -> None:
        self.config = config.storage

        su_sshkey_pri = Path(config.vault_config.tmp, "bitbucket")
        su_sshkey_pub = Path(config.vault_config.tmp, "bitbucket.pub")

        superuser = get_superuser()

        self.git_credentials = GitCredentials(
            "git", su_sshkey_pub, su_sshkey_pri, f"Croixbleue Admin <{superuser.email}>"
        )

    @classmethod
    async def create(
        cls, vault_config: VaultConfig, config: SccsPluginConfig
    ) -> "ManagementStorage":
        self = cls(vault_config, config)

        await self.update_storage()

        return self

    async def update_storage(self):
        """Initialize or update the backend storage

        The storage provides all configuration files required to check or add a repository
        """
        storage_callbacks = pygit2.RemoteCallbacks(
            credentials=self.git_credentials.for_pygit2()
        )

        if self.config_repository is None or self.config_origin is None:
            # path to .git directory in bitbucket-management-storage clone
            git_storage = os.path.join(self.config.path, ".git")

            if os.path.isdir(git_storage):
                self.config_repository = pygit2.Repository(git_storage)
                self.config_origin = self.config_repository.remotes["origin"]
            else:
                # clone anew
                logger.debug("git: cloning bitbucket-remote-storage")
                self.config_repository = pygit2.clone_repository(
                    self.config.git,
                    self.config.path,
                    callbacks=storage_callbacks,
                )
                if self.config_repository is None:
                    raise SccsException("failed to clone repository {self.config.git}")
                self.config_origin = self.config_repository.remotes["origin"]
                logger.debug("git: cloned bitbucket-remote-storage")
                return

        logger.debug("git: pulling from bitbucket-remote-storage")

        tx = self.config_origin.fetch(callbacks=storage_callbacks)
        while tx.total_objects != tx.received_objects:
            await sleep(2)

        self.config_repository.checkout(
            refname="refs/remotes/origin/master", strategy=pygit2.GIT_CHECKOUT_FORCE
        )

        logger.debug("git: pull complete")

    def get_storage_definition(self, slug: str):
        path = Path(self.config.path, "repositories", f"{slug}.json")
        return StorageDefinition.parse_file(path)

    def get_repository_configuration(self, key: str):
        path = Path(self.config.path, "configurations", f"{key}.json")
        return RepositoryConfiguration.parse_file(path)

    def get_repository_privileges(self, key: str):
        with open(f"{self.config.path}/privileges/{key}.json", "r") as f:
            return Privileges(json.load(f))

    def get_ssh_keys(self, configuration: RepositoryConfiguration) -> dict[str, SshKey]:
        result = {}
        for name in configuration.sshKeys:
            path = Path(self.config.path, "sshkeys", f"{name}.json")
            result[name] = SshKey.parse_file(path)
        return result

    def get_branch_restrictions(
        self, configuration: RepositoryConfiguration
    ) -> dict[str, BranchRestriction]:
        result = {}
        for branch_restriction in configuration.branchRestrictions:
            with open(
                f"{self.config.path}/restrictions/{branch_restriction.restrictions}.json",
                "r",
            ) as f:
                result[branch_restriction.restrictions] = Restriction(json.load(f))
        return result

    def load_storage_definitions(
        self, repo_slug: str, storage_definition: StorageDefinition | None = None
    ):
        """Load and return all definitions components involved to "understand" a
        repository configuration

        - repository itself (only if storage_definition is None)
        - configuration
        - restrictions
        - privileges
        - sshkeys
        """

        logger.debug(f"{repo_slug}: loading definitions files")

        # repository
        if storage_definition is None:
            path = Path(self.config.path, "repositories", f"{repo_slug}.json")
            storage_definition = StorageDefinition.parse_file(path)

        # - configurations/
        cache_name = storage_definition.repository.configuration
        path = Path(self.config.path, "configurations", f"{cache_name}.json")
        configuration = RepositoryConfiguration.parse_file(path)

        # - restrictions/
        restrictions_cache = {}
        for branch_restriction in configuration.branchRestrictions:
            cache_name = branch_restriction.restrictions
            path = Path(self.config.path, "restrictions", f"{cache_name}.json")
            restrictions_cache[cache_name] = BranchRestriction.parse_file(path)

        # - privileges/
        cache_name = storage_definition.repository.privileges
        path = Path(self.config.path, "privileges", f"{cache_name}.json")
        with open(f"{self.config.path}/privileges/{cache_name}.json", "r") as f:
            privileges = Privileges(json.load(f))

        # - sshkeys/
        sshkeys_cache = {}
        for name in configuration.sshKeys:
            path = Path(self.config.path, "sshkeys", f"{name}.json")
            sshkeys_cache[cache_name] = SshKey.parse_file(path)

        return (
            storage_definition,
            configuration,
            restrictions_cache,
            privileges,
            sshkeys_cache,
        )

    def global_report(self):
        with open(f"{self.config.path}/reports/global.json", "r") as f:
            return json.load(f)
