# Copyright 2019 mickybart

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from devops_console.config import Config
from .core import Core

_core = None


def getCore(config: Config | None = None) -> Core:
    """Get a unique core

    Returns:
        Core: a common core instance
    """
    global _core
    if _core is None:
        _core = Core(config)

    return _core
