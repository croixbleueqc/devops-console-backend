"""Core module"""

# Copyright 2019 mickybart
# Copyright 2020 Croix Bleue du Québec

# This file is part of devops-console-backend.

# devops-console-backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# devops-console-backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with devops-console-backend.  If not, see <https://www.gnu.org/licenses/>.

from typing import Any, List
from ..config import Config
from .kubernetes import Kubernetes
from .OAuth2 import OAuth2
from .sccs import Sccs


class Core:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.sccs = Sccs(self.config.get("sccs", {}))
        self.kubernetes = Kubernetes(self.config.get("kubernetes", {}), self.sccs)
        self.OAuth2 = OAuth2(self.config.get("OAuth2", {}))

    def startup_background_tasks(self) -> List[Any]:
        return [self.sccs.init, self.kubernetes.init, self.OAuth2.init]

    def cleanup_background_tasks(self) -> List[Any]:
        return []
