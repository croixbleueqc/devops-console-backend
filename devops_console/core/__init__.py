from loguru import logger
import pickle

from .settings import Settings

settings: Settings


try:
    with open("settings.pickle", "rb") as f:
        settings = pickle.load(f)
    logger.info("Loaded settings from 'settings.pickle'")
except FileNotFoundError:
    logger.warning("Pickled settings not found; creating new settings object")
    settings = Settings()  # type: ignore
