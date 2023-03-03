from typing import Literal

from pydantic import BaseModel, Field

from devops_console.sccs.schemas.config import SccsConfig


class APIConfig(BaseModel):
    title: str
    version: str
    description: str
    swagger: dict[Literal["url"], str]


class KubernetesConfig(BaseModel):
    config_dir: str
    suffix_map: dict[str, str]


class OAuth2ConfigConfig(BaseModel):
    Issuer: str
    kAuth: str
    kAccessToken: str
    clientID: str
    kScope: str


class OAuth2Config(BaseModel):
    config: OAuth2ConfigConfig = Field(..., alias="Config")


class UserConfig(BaseModel):
    api: APIConfig
    kubernetes: KubernetesConfig
    sccs: SccsConfig
    OAuth2: OAuth2Config
