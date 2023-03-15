import os
import pickle
from pathlib import Path


picklepath = Path(os.environ["PICKLEJAR"])


def get_superuser():
    with Path(picklepath, "superuser.pickle").open("rb") as f:
        return pickle.load(f)


def get_vaultconfig():
    with Path(picklepath, "vaultconfig.pickle").open("rb") as f:
        return pickle.load(f)
