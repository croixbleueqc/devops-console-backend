import os
import pickle
from pathlib import Path

from loguru import logger

from devops_console.core.settings import Settings

settings: Settings

settingspickle = Path(os.environ["PICKLEJAR"], "settings.pickle")

try:
    with settingspickle.open("rb") as f:
        settings = pickle.load(f)
    logger.info("Loaded settings from 'settings.pickle'")
except FileNotFoundError:
    logger.warning(f"Pickled settings not found in {settingspickle}; creating new settings object")
    settings = Settings()  # type: ignore
