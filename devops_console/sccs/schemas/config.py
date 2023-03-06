from typing import Pattern

from pydantic import BaseModel, Extra, EmailStr

from devops_console.sccs.schemas.provision import ProvisionConfig

class WatcherCreds(BaseModel):
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


class PluginConfig(BaseModel, extra=Extra.allow):
    team: str
    watcher: WatcherCreds
    continuous_deployment: ContinuousDeployment
    storage: Storage
    escalation: dict[str, EscalationDetails]
    blacklist: list[Pattern] = []


class Plugins(BaseModel):
    external: str
    builtin: dict[str, bool]
    config: dict[str, PluginConfig]

class HookServer(BaseModel):
    host: str
    port: int
class SccsConfig(BaseModel ):
    plugins: Plugins
    provision: ProvisionConfig
    hook_server: HookServer
