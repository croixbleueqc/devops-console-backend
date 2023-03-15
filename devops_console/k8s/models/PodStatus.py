from pydantic import BaseModel


class PodStatus(BaseModel):
    name: str
    namespace: str
    cluster: str
