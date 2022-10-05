import os
from loguru import logger
from pathlib import Path
import pickle

from .settings import Settings

settings: Settings

settingspickle = Path(os.environ["PICKLEJAR"], "settings.pickle")

try:
    with settingspickle.open("rb") as f:
        settings = pickle.load(f)
    logger.info("Loaded settings from 'settings.pickle'")
except FileNotFoundError:
    logger.warning("Pickled settings not found; creating new settings object")
    settings = Settings()  # type: ignore
