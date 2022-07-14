from __future__ import annotations

from collections import UserDict
from threading import RLock
from typing import (
    Any,
    ItemsView,
    Iterator,
    KeysView,
    TypeVar,
    ValuesView,
)


K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")


class ThreadsafeCache(UserDict[K, V]):
    """
    A simple cache to help reduce expensive API calls.
    """

    def __init__(self, dict=None, /, **kwargs):
        super().__init__(dict, **kwargs)
        self._lock = RLock()

    def __len__(self) -> int:
        with self._lock:
            return super().__len__()

    def __getitem__(self, key: K) -> V:
        with self._lock:
            return super().__getitem__(key)

    def __setitem__(self, key: K, item: V) -> None:
        with self._lock:
            super().__setitem__(key, item)

    def __delitem__(self, key: K) -> None:
        with self._lock:
            super().__delitem__(key)

    def __iter__(self) -> Iterator[K]:
        with self._lock:
            return super().__iter__()

    def __contains__(self, key: object) -> bool:
        with self._lock:
            return super().__contains__(key)

    def __repr__(self) -> str:
        with self._lock:
            return super().__repr__()

    def __or__(self, other):
        with self._lock:
            return super().__or__(other)

    def __ror__(self, other):
        with self._lock:
            return super().__ror__(other)

    def __ior__(self, other):
        with self._lock:
            return super().__ior__(other)

    def __copy__(self):
        with self._lock:
            return super().__copy__()

    def copy(self):
        with self._lock:
            return super().copy()

    def clear(self) -> None:
        with self._lock:
            super().clear()

    def items(self) -> ItemsView[K, V]:
        with self._lock:
            return super().items()

    def keys(self) -> KeysView[K]:
        with self._lock:
            return super().keys()

    def values(self) -> ValuesView[Any]:
        with self._lock:
            return super().values()

    def pop(self, key: K, default: object = None) -> Any:
        with self._lock:
            return super().pop(key, default)

    def popitem(self) -> tuple[K, V]:
        with self._lock:
            return super().popitem()

    def setdefault(self, key: K, default: V | None = None):
        with self._lock:
            try:
                return self[key]
            except KeyError:
                if default is not None:
                    self[key] = default
            return default

    def update(self, other=(), /, **kwargs: V) -> None:
        with self._lock:
            return super().update(other, **kwargs)
