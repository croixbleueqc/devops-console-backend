import contextlib
from datetime import timedelta

from atlassian.bitbucket import Cloud
from atlassian.bitbucket.cloud.repositories import Repository
from fastapi import HTTPException
from loguru import logger
from requests import HTTPError

from devops_console.schemas.sccs import Commit, DeploymentStatus
from devops_sccs.errors import SccsException
from devops_sccs.redis import cache_sync
from devops_sccs.schemas.config import SccsConfig, Plugins, PluginConfig, EnvironmentConfiguration
from devops_sccs.typing.credentials import Credentials


# FIXME temporary hardcode
def get_plugin_config(plugins_config: Plugins) -> PluginConfig:
    return plugins_config.config.get("cbq")


class SccsV2:
    _instance = None
    config: PluginConfig

    def __new__(cls, config: SccsConfig):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls.config = get_plugin_config(config.plugins)
            cls.environment_configurations = cls.config.continuous_deployment.environments
            cls.admin_session = Cloud(
                username=cls.config.watcher.user,
                password=cls.config.watcher.pwd,
                )
        return cls._instance

    @contextlib.contextmanager
    def session(self, credentials: Credentials | None) -> Cloud:
        if credentials is None:
            session = self.admin_session
        else:
            session = Cloud(username=credentials.user, password=credentials.apikey)

        yield session

        session.close()

    @cache_sync(ttl=timedelta(minutes=15))
    def get_versions(
            self,
            *,
            credentials: Credentials,
            slug: str,
            top: str | None
            ) -> list[Commit]:
        """
        Returns 10 commits for the repositories reverse chronological order starting from the most
        recent, or from the commit hash given as the `top` parameter. This allows the caller to load
        sequential "pages" of commits.

        It is the caller's responsibility to ensure the hash used as `top` is part of the
        repository's main branch history. Typically, it's value will be the hash of the last commit
        retrieved in the previous call to this function.
        """
        commits = []
        with self.session(credentials) as session:
            repository = session.workspaces.get(self.config.team).repositories.get(slug)
            mainbranch = repository.get_data("mainbranch").get("name")
            path = f"/commits/{mainbranch if top is None else top}"

            # when `top` is given, we query for one extra commit and discard the commit
            # corresponding to `top`
            skip_first = top is not None

            res = repository.get(path, params={"pagelen": 11 if skip_first else 10})

            try:
                values = iter(res["values"])

                if skip_first:
                    next(values)

                for commit_data in values:
                    commit = commit_from_api_dict(commit_data)
                    commits.append(commit)

                    if len(commits) == 10:
                        break
            except KeyError as e:
                logger.error(str(e))
                raise HTTPException(status_code=500, detail=str(e))

        return commits

    @cache_sync(ttl=timedelta(hours=1))
    def get_deployment_statuses(
            self,
            *,
            credentials: Credentials,
            slug: str,
            accepted_environments: list[str] | None
            ) -> list[DeploymentStatus]:

        # get actual deployment environments
        environment_configurations: list[EnvironmentConfiguration]
        if accepted_environments is None:
            environment_configurations = self.environment_configurations
        else:
            environment_configurations = [e for e in self.environment_configurations if
                                          e in accepted_environments]

        deployment_statuses = []
        # map environments to DeploymentStatuses
        for environment_configuration in environment_configurations:
            deployment_status = self.get_deployment_status(
                credentials,
                slug,
                environment_configuration
                )

            if deployment_status is None:
                continue

            deployment_statuses.append(deployment_status)

        return deployment_statuses

    def get_deployment_status(
            self,
            credentials: Credentials,
            slug: str,
            environment_configuration: EnvironmentConfiguration
            ) -> DeploymentStatus | None:
        with self.session(credentials) as session:
            repository = session.workspaces.get(self.config.team).repositories.get(slug)

            commit_hash = self.get_deployment_commit_hash(
                repository,
                environment_configuration
                )

            if commit_hash is None:
                return

            try:
                commit = self.get_commit(credentials, slug, commit_hash)
            except Exception:
                return

            readonly = environment_configuration.trigger.get("enabled", True) and False

            pullrequest = self.get_pullrequest_url(
                repository,
                environment_configuration.branch
                ) if environment_configuration.trigger.get("pullrequest", False) else None

            return DeploymentStatus(
                environment=environment_configuration.name,
                commit=commit,
                readonly=readonly,
                pullrequest=pullrequest
                )

    def get_pullrequest_url(self, repository: Repository, branch_name: str) -> str | None:
        for pr in repository.pullrequests.each():
            if (
                    pr.destination_branch == branch_name and
                    self.config.continuous_deployment.pullrequest.tag in pr.title
            ):
                link = pr.get_link("html")
                return link["href"] if type(link) is dict else link

    def get_deployment_commit_hash(
            self,
            repository: Repository,
            environment_configuration: EnvironmentConfiguration
            ) -> str | None:
        try:
            branch = repository.branches.get(environment_configuration.branch)
        except HTTPError:
            return

        version_file_name = environment_configuration.version.get("file")
        deployment_commit_hash: str
        if version_file_name is not None:
            response = repository.get(
                f"src/{branch.hash}/{version_file_name}",
                not_json_response=True
                )
            if response is None:
                raise SccsException(
                    f"failed to get version from {version_file_name} for {repository.name} on branch {branch.name}"
                    )
            deployment_commit_hash = response.decode("utf-8").strip()
        elif environment_configuration.version.get("git", False):  # TODO this is unclear
            deployment_commit_hash = branch.hash  # main branch
        else:
            raise NotImplementedError()

        return deployment_commit_hash

    def get_commit(self, credentials: Credentials, slug: str, commit_hash: str) -> Commit:
        with self.session(credentials) as session:
            repository = session.workspaces.get(self.config.team).repositories.get(slug)
            try:
                commit_dict = repository.get(f"/commit/{commit_hash}")
            except HTTPError as e:
                logger.warning(e)
                raise

            return commit_from_api_dict(commit_dict)


def commit_from_api_dict(commit_dict: dict) -> Commit:
    try:
        return Commit(
            hash=commit_dict["hash"],
            message=commit_dict["message"].strip(),
            date=commit_dict["date"],
            author=commit_dict["author"]["raw"]
            )
    except KeyError as e:
        logger.error(str(e))
        raise e
