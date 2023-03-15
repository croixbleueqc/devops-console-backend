from typing import Pattern

from pydantic import BaseModel, Extra, EmailStr

from .provision import ProvisionConfig


class WatcherCreds(BaseModel):
    """
    Admin credentials # TODO: rename to admin or superuser or something...
    """

    user: str
    pwd: str
    email: EmailStr | None = None


class EnvironmentConfiguration(BaseModel):
    name: str
    branch: str
    version: dict[str, str]
    trigger: dict[str, bool] = {}


class PullRequest(BaseModel):
    tag: str


class Pipeline(BaseModel):
    versions_available: list[str]


class ContinuousDeployment(BaseModel):
    environments: list[EnvironmentConfiguration]
    pullrequest: PullRequest
    pipeline: Pipeline


class Storage(BaseModel):
    path: str
    git: str
    repo: str


class EscalationDetails(BaseModel):
    repository: str
    permissions: list[str]


class VaultConfig(BaseModel):
    skip_vault: bool = False
    tmp: str
    vault_secret: str
    vault_mount: str


class SccsPluginConfig(BaseModel, extra=Extra.allow):
    # Bitbucket "worspace" | GitLab "owner" | "organization"
    team: str
    watcher: WatcherCreds
    continuous_deployment: ContinuousDeployment
    storage: Storage
    vault_config: VaultConfig
    escalation: dict[str, EscalationDetails]
    blacklist: list[Pattern] = []


class SccsPlugins(BaseModel):
    external: str
    builtin: dict[str, bool]
    config: dict[str, SccsPluginConfig]


class HookServer(BaseModel):
    host: str
    port: int


class SccsConfig(BaseModel):
    plugins: SccsPlugins
    provision: ProvisionConfig
    hook_server: HookServer
