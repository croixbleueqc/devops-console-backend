from __future__ import annotations
from typing import Dict, List
from pydantic import BaseModel


class WatcherCreds(BaseModel):
    user: str
    pwd: str


class Environment(BaseModel):
    name: str
    branch: str
    version: Dict[str, str]
    trigger: Dict[str, bool] = {}


class PullRequest(BaseModel):
    tag: str


class Pipeline(BaseModel):
    versions_available: List[str]


class Storage(BaseModel):
    path: str
    git: str
    repo: str


class SU(BaseModel):
    skip_vault: bool = False
    tmp: str
    vault_secret: str
    vault_mount: str


class EscalationDetails(BaseModel):
    repository: str
    permissions: List[str]


class ContinuousDeployment(BaseModel):
    environments: List[Environment]
    pullrequest: PullRequest
    pipeline: Pipeline


class CbqConfig(BaseModel):
    team: str
    watcher: WatcherCreds
    continuous_deployment: ContinuousDeployment
    storage: Storage
    su: SU
    escalation: Dict[str, EscalationDetails]
