from typing import Callable
from pydantic import BaseModel, EmailStr


class AppPasswords(BaseModel):
    bitbucket_management: str
    snyk: str

    class Config:
        alias_generator: Callable[[str], str] = lambda s: s.replace("-", "_")


class VaultBitbucket(BaseModel):
    app_passwords: AppPasswords | None = None
    email: EmailStr
    private_key: str
    public_key: str
    pwd: str
    username: str
