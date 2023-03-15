from pydantic import BaseModel


class Container(BaseModel):
    pass


class PodStatus(BaseModel):
    name: str
    containers: list[Container]
