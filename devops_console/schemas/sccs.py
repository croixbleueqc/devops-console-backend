from pydantic import BaseModel


class Commit(BaseModel):
    hash: str
    message: str
    date: str
    author: str


class DeploymentStatus(BaseModel):
    environment: str
    commit: Commit
    readonly: bool
    pullrequest: str | None
