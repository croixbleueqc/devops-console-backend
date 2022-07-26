"""
Configuration module to parse json configuration files correctly

Config files are stored in the config folder inside the module.

the BRANCH_NAME determines the configuration to load.

Config will merge (listed as less to more important):
- default.json
- <BRANCH_NAME>.json
- local.json

In addition, Config will replace all {env} string in a json file to the BRANCH_NAME value.

"""

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


from collections import UserDict
import contextlib
import json
import logging
import os
from copy import deepcopy
from functools import reduce
from pathlib import Path
import sys
from typing import Any


class Config(UserDict):
    """
    Configuration class
    """

    def __init__(self, path: Path | None = None):
        super().__init__()

        if path is None:
            self.dir_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "config"
            )
        elif path.is_dir():
            self.dir_path = str(path)
        else:
            logging.error("path parameter must be a valid directory.")
            sys.exit(1)

        if os.environ.get("BRANCH_NAME") is None:
            os.environ["BRANCH_NAME"] = "undefined"

        config = self.__load_config()
        self.update(config)

        self.__deep_replace(self, env=os.environ["BRANCH_NAME"])
        logging.debug(config)

    def use_resource(self, resource):
        return "{dir}/resources/{resource}".format(dir=self.dir_path, resource=resource)

    def __load_config(self):
        default = self.__load_config_file("default")
        env = self.__load_config_file(os.environ["BRANCH_NAME"])
        local = self.__load_config_file("local")

        # Order is important inside the list
        return reduce(self.__deep_merge, [{}, default, env, local])

    def __load_config_file(self, file_name):
        file_path = "{dir}/config/{name}.json".format(dir=self.dir_path, name=file_name)
        return self.__load_json(file_path)

    def __load_json(self, json_file):
        """Load JSON file

        Args:
            json_file (str): filename of a json file

        Returns:
            dict: content of the file
        """
        try:
            with open(json_file) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def __deep_merge(
        self, dict_base: dict[str, Any], dict_custom: dict[str, Any]
    ) -> dict[str, str]:
        result = deepcopy(dict_base)
        for key, value in dict_custom.items():
            if isinstance(value, dict):
                node = result.setdefault(key, {})
                mergedNode = self.__deep_merge(node, value)
                result[key] = mergedNode
            else:
                result[key] = value

        return result

    def __deep_replace(self, dict_base, **kwargs) -> None:
        for name, value in dict_base.items():
            if isinstance(value, dict):
                self.__deep_replace(value, **kwargs)
            elif isinstance(value, str):
                with contextlib.suppress(IndexError):
                    dict_base[name] = value.format(**kwargs)
