from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    plugin_id: str
    bitbucket_username: str
    bitbucket_app_password: str


class UserCreate(UserBase):
    email: EmailStr
    plugin_id: str
    bitbucket_username: str
    bitbucket_app_password: str
    password: str


class UserUpdate(UserBase):
    password: str | None = None


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class UserInDB(UserBase):
    hashed_password: str
