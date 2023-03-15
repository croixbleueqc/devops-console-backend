"""
This madule contains models corresponding to the files in the top-level
config directory.
"""

from typing import Literal

from pydantic import BaseModel, Field

from .sccs_config import SccsConfig


class APIConfig(BaseModel):
    title: str
    version: str
    description: str
    swagger: dict[Literal["url"], str]


class KubernetesConfig(BaseModel):
    config_dir: str
    suffix_map: dict[str, str]


class OAuth2ConfigConfig(BaseModel):
    issuer: str = Field(..., alias="Issuer")
    kAuth: str
    kAccessToken: str
    clientID: str
    kScope: str


class OAuth2Config(BaseModel):
    config: OAuth2ConfigConfig = Field(..., alias="Config")


class UserConfig(BaseModel):
    """Top-Level configuration for the entire application"""

    api: APIConfig
    kubernetes: KubernetesConfig
    sccs: SccsConfig
    oAuth2: OAuth2Config = Field(..., alias="OAuth2")
