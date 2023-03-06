
from devops_console.sccs.schemas.provision import ProvisionConfig


class ProvisionV2:
    def __init__(self, config: ProvisionConfig) -> None:
        self.config = config
