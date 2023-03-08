import os
from pathlib import Path
from kubernetes_asyncio.client.api_client import json

import pygit2
from anyio import sleep
from loguru import logger

from devops_console.sccs.errors import SccsException

from .storage_helpers import get_superuser

from .provision import GitCredentials
from .schemas.config import PluginConfig, VaultConfig


class SccsStorageWriter:
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

    def __init__(self, vault_config: VaultConfig, config: PluginConfig) -> None:
        self.config = config.storage

        su_sshkey_pri = Path(vault_config.tmp, "bitbucket")
        su_sshkey_pub = Path(vault_config.tmp, "bitbucket.pub")

        superuser = get_superuser()

        self.git_credentials = GitCredentials(
            "git", su_sshkey_pub, su_sshkey_pri, f"Croixbleue Admin <{superuser.email}>"
        )

    @classmethod
    async def create(cls, vault_config: VaultConfig, config: PluginConfig) -> "SccsStorageWriter":
        self = cls(vault_config, config)
        # TODO: this method was created to allow running the async method update_storage
        # during the plugin initialization. But the method in question isn't behaving properly
        # in a local environment. It's not clear why yet...
        await self.update_storage()

        return self

    async def update_storage(self):
        """Initialize or update the backend storage

        The storage provides all configuration files required to check or add a repository
        """
        storage_callbacks = pygit2.RemoteCallbacks(credentials=self.git_credentials.for_pygit2())

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
                logger.debug("cloned")
                return

        logger.debug("git: pulling from bitbucket-remote-storage")
        # make the type checker happy
        if self.config_origin is None or self.config_repository is None:
            raise SccsException("Failed to initialize storage.")

        tx = self.config_origin.fetch(callbacks=storage_callbacks)
        while tx.total_objects != tx.received_objects:
            await sleep(2)

        self.config_repository.checkout(
            refname="refs/remotes/origin/master", strategy=pygit2.GIT_CHECKOUT_FORCE
        )

        logger.debug("cbq: pull complete")

    def load_storage_definitions(self, repo_slug: str, storage_definition=None):
        """Load and return all definitions components involved to "understand" a repository configuration

        - repository itself (only if storage_definition is None)
        - configuration
        - restrictions
        - privileges
        - sshkeys
        """

        logger.debug(f"{repo_slug}: loading definitions files")

        # repository
        if storage_definition is None:
            with open(f"{self.config.path}/repositories/{repo_slug}.json", "r") as f:
                storage_definition = json.load(f)

        # - configurations/
        cache_name = storage_definition["repository"]["configuration"]
        with open(f"{self.config.path}/configurations/{cache_name}.json", "r") as f:
            configuration = json.load(f)

        # - restrictions/
        restrictions_cache = {}
        for branch_restriction in configuration.get("branchRestrictions", []):
            cache_name = branch_restriction["restrictions"]
            with open(f"{self.config.path}/restrictions/{cache_name}.json", "r") as f:
                restrictions_cache[cache_name] = json.load(f)

        # - privileges/
        cache_name = storage_definition["repository"]["privileges"]
        with open(f"{self.config.path}/privileges/{cache_name}.json", "r") as f:
            privileges = json.load(f)

        # - sshkeys/
        sshkeys_cache = {}
        for sshkey in configuration.get("sshKeys", []):
            cache_name = sshkey
            with open(f"{self.config.path}/sshkeys/{cache_name}.json", "r") as f:
                sshkeys_cache[cache_name] = json.load(f)

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
