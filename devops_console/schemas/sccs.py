from pydantic import BaseModel

from devops_console.sccs.schemas.provision import ContractArg, MainContract, RepositoryContract


class Commit(BaseModel):
    hash: str
    message: str
    date: str
    author: str


class DeploymentStatus(BaseModel):
    environment: str
    commit: Commit
    readonly: bool
    pullrequest: str | None


class RepositoryDescription(BaseModel):
    name: str
    slug: str
    url: str | None
    permission: str = "none"


class RepositoryCollectionEnvironmentConfig(BaseModel):
    name: str
    enabled: bool


class RepositoryCollection(BaseModel):
    name: str
    repositories: list[str]
    environments: list[RepositoryCollectionEnvironmentConfig]


class AddRepositoryContract(BaseModel):
    main: MainContract
    repository: RepositoryContract
    templates: dict[str, dict[str, ContractArg]]


class TriggerCDReturnType(BaseModel):
    environment: str
    version: str
    author: str | None
    date: str | None
    pullrequest: str | None
    readonly: bool


class Project(BaseModel):
    name: str
    key: str
    description: str | None
    is_private: bool
    created_on: str
    updated_on: str
