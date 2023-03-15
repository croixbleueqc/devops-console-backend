"""Models for parsing the "provision" section of the user config file.

TODO: there are lots of "aliases" in here because the config field names were poorly 
chosen. Rename the fields in the JSON config directly to match the names of the fields 
in the models.
"""

import abc
import enum

from typing import Any, TypeAlias
from pydantic import BaseModel, Field


class TemplateConfiguration(BaseModel):
    """Basic configuration information for a template."""

    git_url: str = Field(
        ...,
        regex=r"(^git@bitbucket\.org:croixbleue/[a-zA-Z0-9-_]+\.git$|^https://"
        r"[w]{0,3}\.?github.com/croixbleueqc/[a-zA-Z0-9-_]+(.git)?$)",
        alias="git",
    )
    main_branch_name: str = Field(..., alias="main_branch")
    other_branch_names: list[str] = Field([], alias="other_branches")


class TemplateFieldType(str, enum.Enum):
    string = "string"
    boolean = "bool"
    integer = "integer"


TemplateFieldValue: TypeAlias = str | bool | int


class TemplateArgumentField(BaseModel):
    type: TemplateFieldType
    description: str
    required: bool = False
    default: int | str | bool | None
    validator: str | None
    arg: str | dict[str, Any]


class TemplateInitializationCommand(BaseModel):
    """A schematized command to be run in the repository after it has been created."""

    cmd: list[str] = []
    args: dict[str, TemplateArgumentField] = {}


class RepositoryTemplate(BaseModel):
    """Describes a template for the creation of a new repository."""

    configuration: TemplateConfiguration = Field(alias="from")
    init_cmd: TemplateInitializationCommand = Field(
        TemplateInitializationCommand(), alias="setup"
    )


class ConfigurationValue(BaseModel):
    key: str
    name: str | None
    description: str | None


class ConfigurationFieldType(str, enum.Enum):
    suggestion = "suggestion"
    # TODD: do we even need this?


class ConfigurationField(BaseModel, abc.ABC):
    type: ConfigurationFieldType
    description: str
    required: bool = False
    default: int | None
    values: list[ConfigurationValue]


class MainContract(BaseModel):
    # A regex used to validate the repository name.
    slug_regex: str = Field(..., alias="repository_validator")
    template_required: bool


class RepositoryContract(BaseModel):
    project: ConfigurationField
    configuration: ConfigurationField
    privileges: ConfigurationField


class ProvisionConfig(BaseModel):
    # local path where clones of new repositories will be created
    checkout_base_path: str
    main_contract: MainContract = Field(alias="main")
    repository_contract: RepositoryContract = Field(alias="repository")
    repository_templates: dict[str, RepositoryTemplate] = Field(alias="templates")


class NewRepositoryDefinition(BaseModel):
    """Values corresponding to the fields of a repository contract."""

    slug: str
    configuration: ConfigurationValue
    privileges: ConfigurationValue
    project: ConfigurationValue
