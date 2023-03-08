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

from .kubernetes import Kubernetes
from .oauth2 import OAuth2
from .sccs import Sccs
from .sccs_v2 import SccsV2
from ..core import settings
from ..schemas import UserConfig


class CoreClient:
    """Singleton class containing the core crud clients."""
    _instance = None
    config: UserConfig
    sccs: Sccs
    kubernetes: Kubernetes
    oauth2: OAuth2

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)

            cls.config = settings.userconfig
            cls.sccs = Sccs(cls.config.sccs)
            cls.sccs_v2 = SccsV2(cls.config.sccs)
            cls.kubernetes = Kubernetes(cls.config.kubernetes, cls.sccs)
            cls.oauth2 = OAuth2(cls.config.OAuth2)

        return cls._instance

    def startup_tasks(self) -> list:
        return [self.sccs.init, self.kubernetes.init, self.oauth2.init]

    def shutdown_tasks(self) -> list:
        return []
