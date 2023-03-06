from typing import Any, TypeAlias
from pydantic import BaseModel, Field


class From(BaseModel):
    git: str = Field(
        ...,
        regex=r"(^git@bitbucket\.org:croixbleue/[a-zA-Z0-9-_]+\.git$|^https://"
        r"[w]{0,3}\.?github.com/croixbleueqc/[a-zA-Z0-9-_]+(.git)?$)",
    )
    main_branch: str
    other_branches: list[str] = []


class ContractArg(BaseModel):
    type: str
    description: str
    required: bool = False
    default: Any | None
    validator: str | None
    arg: str | dict[str, Any] | None


class TemplateSetup(BaseModel):
    cmd: list[str] | None
    args: dict[str, ContractArg] | None


class Template(BaseModel):
    from_: From = Field(alias="from")
    setup: TemplateSetup


class MainContract(BaseModel):
    repository_validator: str
    template_required: bool


class RepoContractProjectValue(BaseModel):
    name: str
    key: str


class RepoContractProject(ContractArg):
    roleName: str
    values: list[RepoContractProjectValue]


class RepoContractConfigValue(BaseModel):
    short: str
    key: str


class RepoContractConfig(ContractArg):
    default: int
    roleName: str
    values: list[RepoContractConfigValue]


class RepoContractPrivileges(ContractArg):
    roleName: str
    values: list[RepoContractConfigValue]


class RepositoryContract(BaseModel):
    project: RepoContractProject
    configuration: RepoContractConfig
    privileges: RepoContractPrivileges


class ProvisionConfig(BaseModel):
    checkout_base_path: str
    main_contract: MainContract = Field(alias="main")
    repository_contract: RepositoryContract = Field(alias="repository")
    templates: dict[str, Template]


class AddRepositoryDefinition(BaseModel):
    name: str
    configuration: RepoContractConfigValue
    privileges: RepoContractConfigValue
    project: RepoContractProjectValue


TemplateParams: TypeAlias = dict[str, dict]
