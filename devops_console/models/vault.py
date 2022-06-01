from typing import Callable
from pydantic import BaseModel, EmailStr


def kebab_snake(s: str):
    return s.replace("_", "-")


class AppPasswords(BaseModel):
    bitbucket_management: str
    snyk: str

    class Config:
        alias_generator = kebab_snake


class VaultBitbucket(BaseModel):
    app_passwords: AppPasswords
    email: EmailStr
    private_key: str
    public_key: str
    pwd: str
    username: str
