import contextlib
import json
from pathlib import Path

from loguru import logger


def read_json_file(path: Path) -> dict:
    try:
        json_str = path.read_text()
        d = json.loads(json_str)
    except FileNotFoundError:
        logger.warning(f"File {path} not found")
        return {}
    return d


def deep_replace(dict_base: dict, **kwargs) -> dict:
    for name, value in dict_base.items():
        if isinstance(value, dict):
            deep_replace(value, **kwargs)
        elif isinstance(value, str):
            with contextlib.suppress(IndexError):
                dict_base[name] = value.format(**kwargs)

    return dict_base
