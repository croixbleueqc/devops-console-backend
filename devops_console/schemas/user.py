from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    plugin_id: str
    bitbucket_username: str
    bitbucket_app_password: str

    @property
    def author(self):
        return f"{self.full_name} <{self.email}>"


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str | None = None


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class UserInDB(UserBase):
    hashed_password: str
