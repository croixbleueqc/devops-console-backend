from pydantic import BaseModel

class Container(BaseModel):


class PodStatus(BaseModel):
    name: str
    containers: list[Container]