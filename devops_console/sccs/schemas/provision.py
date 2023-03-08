from typing import Any, Literal, TypeAlias
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


# Bitbucket Management Storage Models

"""
Repository structure

{
    "repository": {
        "name": "<Name of the repository>",
        "project": "<Bitbucket key project>",
        "configuration": "<configuration name in configurations/ folder>",
        "privileges": "<privilege name in privileges/ folder>"
    },
    "template": "<Template name or empty string>",
    "template_params": <Template object parameters or null>
}

"""


class RepositoryDefinition(BaseModel):
    name: str
    project: str
    configuration: str
    privilege: str


TemplateName: TypeAlias = str

TemplateParams: TypeAlias = dict[str, bool | str] | None


class RepositoryStructure(BaseModel):
    repository: RepositoryDefinition
    template: TemplateName
    template_params: TemplateParams


"""
Restrictions

Bitbucket restrictions for branches
Restriction structure

{
    "<key>": <value or null>,
    ...
}
"""
Restriction: TypeAlias = dict[str, str | None]


class BranchRestriction(BaseModel):
    """Maps a branch name to a restriction"""

    branchPattern: str
    # refers to the name of a restriction defined in restrictions/
    restrictions: str


"""
Configurations

Store all configurations definitions
Configuration structure

{
    "managed": true | false,
    "private": true,
    "forkPolicy": "no_public_forks",
    "mainBranch": "",
    "otherBranches": [
        "deploy/dev",
        ...
    ],
    "branchRestrictions": [
        {
            "branchPattern": "",
            "restrictions": "<restriction name in restrictions/ folder"
        },
        ...
    ],
    "pipelines": {
        "enabled": true | false
    }
}
"""


class ConfigurationPipelines(BaseModel):
    enabled: bool


class RepositoryConfiguration(BaseModel):
    managed: bool
    private: bool = False
    forkPolicy: str = "no_public_forks"
    mainBranch: Literal["main", "master"]
    otherBranches: list[str] = []
    branchRestrictions: list[BranchRestriction]
    pipelines: ConfigurationPipelines


"""
Privileges

Store all privileges definitions for bitbucket
Privilege structure

{
    "<group>": "<read | write | admin>",
    ...
}
"""

Privilege: TypeAlias = dict[str, Literal["read", "write", "admin"]]
