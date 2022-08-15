from pydantic import BaseModel, EmailStr, Field


class AppPasswords(BaseModel):
    bitbucket_management: str = Field(..., alias="bitbucket-management")
    snyk: str


class VaultBitbucket(BaseModel):
    app_passwords: AppPasswords
    email: EmailStr
    private_key: str
    public_key: str
    pwd: str
    username: str
