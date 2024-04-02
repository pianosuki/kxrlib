from __future__ import annotations

import os.path
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .kresource_dir import KResourceDir


class KResource(ABC):
    def __init__(self, name: str):
        self.name = name

        self._parent: KResourceDir | None = None
        self._children: dict[str, KResource] | None = None

    @property
    def path(self) -> str:
        if self.parent is None:
            return self.name
        else:
            return os.path.join(self.parent.path, self.name)

    @property
    def parent(self) -> KResource | None:
        return self._parent

    @parent.setter
    def parent(self, value: KResource):
        if self._parent is not None:
            raise PermissionError("Cannot change parent once it has been set")
        if not isinstance(value, KResource):
            raise TypeError(f"Argument 'value' must be {KResource}, not {type(value)}")

        self._parent = value

    @property
    @abstractmethod
    def packed_size(self) -> int | None:
        ...
