from typing import Literal, TypeAlias
from pydantic import BaseModel, Field

# Bitbucket Management Storage Models


class RepositoryDefinition(BaseModel):
    name: str
    project: str
    configuration: str
    privileges: str


TemplateName: TypeAlias = str

TemplateParams: TypeAlias = dict[str, bool | str]


class StorageDefinition(BaseModel):
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

    repository: RepositoryDefinition
    template: TemplateName
    template_params: TemplateParams | None


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

    branch_pattern: str = Field(..., alias="branchPattern")
    # refers to the name of a restriction defined in restrictions/
    restrictions: str


class ConfigurationPipelines(BaseModel):
    enabled: bool


class RepositoryConfiguration(BaseModel):
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
        },
        "sshKeys": ["<sshKey name in sshKeys/ folder"]
    }
    """

    managed: bool
    is_private: bool = Field(defalt=False, alias="private")
    forkPolicy: str = "no_public_forks"
    mainBranch: Literal["main", "master"]
    otherBranches: list[str] = []
    branchRestrictions: list[BranchRestriction] = []
    pipelines: ConfigurationPipelines
    sshKeys: list[str] = []


"""
Privileges

Store all privileges definitions for bitbucket
Privilege structure

{
    "<group>": "<read | write | admin>",
    ...
}
"""
Privileges: TypeAlias = dict[str, Literal["read", "write", "admin"]]


class SshKey(BaseModel):
    """
    SSH keys

    Store all public ssh keys
    public ssh key structure

    {
        "label": "<name of the key>",
        "key": "ssh-rsa ..."
    }

    """

    label: str
    key: str
