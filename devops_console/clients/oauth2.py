# Copyright 2021 Croix Bleue du Québec

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


from ..schemas.userconfig import OAuth2Config


class OAuth2(object):
    """OAuth2 Core"""

    def __init__(self, config: OAuth2Config):
        self.config = config

    async def init(self):
        pass

    async def get_config(self):
        return {
            "Config": {**self.config.config.dict()}
        }  # this ugly hack this has to do with the fact that "Config" is a reserved keyword in pydantic but it's the key expected by the frontend.
