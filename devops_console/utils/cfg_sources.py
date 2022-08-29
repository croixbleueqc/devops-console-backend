import contextlib
from functools import reduce
import json
import logging
import os
from pathlib import Path
import sys
from typing import Literal
from pydantic import BaseSettings

from devops_console.schemas.cbq import SU

from ..schemas.vault import VaultBitbucket
from ..schemas import UserConfig
from ..utils.vault import get_bb_su_creds

_userconfig: UserConfig


def vault_secret_source(
    settings: BaseSettings,
) -> dict[Literal["superuser"], VaultBitbucket]:
    global _userconfig  # OK as long as this function runs after json_userconfig_source
    # TODO determine whether this is the right place to do this
    # TODO also, can we avoid using magic strings?
    su: SU = SU(**_userconfig.sccs.plugins.config["cbq"]["su"])
    bb_secrets = get_bb_su_creds(su)
    return {"superuser": bb_secrets}


def json_userconfig_source(
    settings: BaseSettings,
) -> dict[Literal["userconfig"], UserConfig]:
    """Read and parse json config files."""

    dirpath = "config"

    userconfig = UserConfig.parse_obj(load_json_configs(dirpath))

    global _userconfig
    _userconfig = userconfig

    return {"userconfig": userconfig}


def load_json_configs(dirpath):
    default = load_json_config_file(dirpath, "default") or {}
    env = (
        load_json_config_file(dirpath, os.environ.get("BRANCH_NAME", "undefined")) or {}
    )
    local = load_json_config_file(dirpath, "local") or {}

    if all(v == {} for v in [default, env, local]):
        logging.critical("No config files found, exiting")
        sys.exit(1)

    # Order is important inside the list (last one is the most important)
    dicts = list(filter(lambda x: x != {}, [default, env, local]))
    merged: dict = reduce(lambda a, b: a | b, dicts)

    # replace all 'env' with BRANCH_NAME
    configs = deep_replace(
        merged,
        env=os.environ.get("BRANCH_NAME", "undefined"),
    )

    return configs


def load_json_config_file(directory, file_name):
    file_path = f"{directory}/{file_name}.json"
    try:
        d = json.loads(Path(file_path).read_text())
    except OSError:
        logging.info(f"Could not load {file_path}")
        return {}
    return d


def deep_replace(dict_base, **kwargs) -> None:
    for name, value in dict_base.items():
        if isinstance(value, dict):
            deep_replace(value, **kwargs)
        elif isinstance(value, str):
            with contextlib.suppress(IndexError):
                dict_base[name] = value.format(**kwargs)

    return dict_base
