from __future__ import annotations

import os
from typing import TYPE_CHECKING
from enum import Enum

from .byte_buffer import ByteBuffer
from .resource import KResourceDir, KResourceFile

if TYPE_CHECKING:
    from .kxr_file import KxrFile


class EntryType(Enum):
    ROOT = 0
    DIRECTORY = 1
    FILE = 2


class EntryFlags(Enum):
    DIRECTORY = 1
    LOCKED = 2
    ZIPPED = 4


class KxrHeaderEntry:
    """
    [Header entry format]
    - 0 to 1:           namesize
    - 2 to namesize:    name
    - namesize to +4:   created
    - @ to +4:          updated
    - @ to +1:          flags
    - if flags & 1:
    - - @ to +2:        numchildren
    - else:
    - - @ to +4:        offset
    - - @ to +4:        size
    """

    def __init__(self, kxr_file: KxrFile, entry_type: EntryType = None, name: str = "", created: int = 0, updated: int = 0):
        self.kxr_file = kxr_file
        self._type = entry_type
        self.name = name
        self.created = created
        self.updated = updated

        self._locked: bool | None = False if self._type is EntryType.ROOT else None
        self._zipped: bool | None = False if self._type is EntryType.ROOT else None

        self.offset: int | None = None
        self._size: int | None = None

        self._parent: KxrHeaderEntry | None = None
        self.children: dict[str, KxrHeaderEntry] = {}

    def recursive_read_entries(self, hbbuf: ByteBuffer):
        name = hbbuf.get("t")
        self.name = name if name else self.kxr_file.matched_name
        self.created = hbbuf.get("i")
        self.updated = hbbuf.get("i")
        flags = int.from_bytes(hbbuf.get("b"))

        if self._type is not EntryType.ROOT:
            self.is_dir = flags & 1 != 0
            self.locked = flags & 2 != 0
            self.zipped = flags & 4 != 0

        if self.is_dir:
            num_children = hbbuf.get("s")

            for _ in range(num_children):
                child_entry = KxrHeaderEntry(self.kxr_file)
                child_entry.recursive_read_entries(hbbuf)

                self.add_entry(child_entry)
        else:
            self.offset = hbbuf.get("i")
            self.size = hbbuf.get("i")

    def recursive_write_entries(self, hbbuf: ByteBuffer):
        hbbuf.put("t", self.name)
        hbbuf.put("i", self.created)
        hbbuf.put("i", self.updated)
        hbbuf.put("b", self.flags.to_bytes(1))

        if self.is_dir:
            hbbuf.put("s", len(self.children))

            if self.children:
                for child_entry in self.children.values():
                    child_entry.recursive_write_entries(hbbuf)
        else:
            hbbuf.put("i", self.offset)
            hbbuf.put("i", self.size)

    def add_entry(self, entry: KxrHeaderEntry):
        self.children[entry.name] = entry
        entry.parent = self

    async def get_content(self) -> ByteBuffer:
        if self.is_dir:
            raise IsADirectoryError(f"Must not be a directory to get content from: {self}")

        bbuf = await self.kxr_file.read_from_kxr(self.offset, self.size)

        if not bbuf:
            raise ValueError(f"No data was read: offset='{self.offset}', size='{self.size}' kxr_file={self.kxr_file}")

        if self.zipped:
            bbuf.decompress()
        else:
            bbuf.crypt(self.kxr_file.passhash ^ self.offset)

        return bbuf

    async def put_content(self, name: str, bbuf: ByteBuffer, needs_zipping: bool = True):
        if not self.is_dir:
            raise NotADirectoryError(f"Must be a directory to create content in: {self}")

        entry = self.children.get(name)

        if entry is None:
            entry = KxrHeaderEntry(self.kxr_file)
            entry.name = name
            self.add_entry(entry)

        if needs_zipping:
            bbuf.compress()
        else:
            bbuf.crypt(self.kxr_file.passhash ^ self.kxr_file.datasize)

        entry.offset = self.kxr_file.datasize
        entry.size = bbuf.size
        entry.zipped = needs_zipping

        await self.kxr_file.write_to_kxr(entry.offset, bbuf)

        self.kxr_file.datasize += bbuf.size

    def populate(self, resource_dir: KResourceDir):
        for name, child in resource_dir.children.items():
            if isinstance(child, KResourceFile):
                entry = KxrHeaderEntry(self.kxr_file, entry_type=EntryType.FILE, name=name, created=0, updated=0)

                self.add_entry(entry)
            elif isinstance(child, KResourceDir):
                entry = KxrHeaderEntry(self.kxr_file, entry_type=EntryType.DIRECTORY, name=name, created=0, updated=0)

                self.add_entry(entry)

                entry.populate(child)

    @property
    def is_root(self) -> bool:
        return self._type is EntryType.ROOT

    @property
    def is_dir(self) -> bool:
        return self._type is EntryType.DIRECTORY or self.is_root

    @is_dir.setter
    def is_dir(self, value: bool):
        if self._type is not None:
            raise PermissionError("Cannot change entry type once it has been set")
        if not isinstance(value, bool):
            raise TypeError(f"Argument 'value' must be {bool}, not {type(value)}")

        self._type = EntryType.DIRECTORY if value else EntryType.FILE

    @property
    def locked(self) -> bool:
        return self._locked

    @locked.setter
    def locked(self, value: bool):
        if self._locked is not None:
            raise PermissionError("Cannot change locked state once it has been set")
        if not isinstance(value, bool):
            raise TypeError(f"Argument 'value' must be {bool}, not {type(value)}")

        self._locked = value

    @property
    def zipped(self) -> bool:
        return self._zipped

    @zipped.setter
    def zipped(self, value: bool):
        if self._zipped is not None:
            raise PermissionError("Cannot change zipped state once it has been set")
        if not isinstance(value, bool):
            raise TypeError(f"Argument 'value' must be {bool}, not {type(value)}")

        self._zipped = value

    @property
    def flags(self) -> int:
        return (
            1 if self.is_dir else 0 |
            2 if self.locked else 0 |
            4 if self.zipped else 0
        )

    @property
    def size(self) -> int | None:
        if not self.is_dir:
            return self._size
        else:
            total_size = 0

            for child in self.children.values():
                child_size = child.size

                if isinstance(child_size, int):
                    total_size += child_size

            return total_size if total_size > 0 else None

    @size.setter
    def size(self, size: int):
        if not isinstance(size, int):
            raise TypeError(f"Argument 'size' must be {int}, not {type(size)}")
        if self._size is not None:
            raise PermissionError(f"Cannot change size once it has been set")

        self._size = size

    @property
    def parent(self) -> KxrHeaderEntry | None:
        return self._parent

    @parent.setter
    def parent(self, value: KxrHeaderEntry):
        if self._parent is not None:
            raise PermissionError("Cannot change parent once it has been set")
        if not isinstance(value, KxrHeaderEntry):
            raise TypeError(f"Argument 'value' must be {KxrHeaderEntry}, not {type(value)}")

        self._parent = value

    @property
    def path(self) -> str:
        if self.parent is None:
            return self.name
        else:
            return os.path.join(self.parent.path, self.name)

    @property
    def tree(self) -> dict[str, KxrHeaderEntry | dict]:
        if not self.is_dir:
            raise NotADirectoryError(f"Kxr header entry must be a directory to construct directory tree: {self}")

        tree = {}

        for name, child in self.children.items():
            if not child.is_dir:
                tree[name] = child
            else:
                tree[name] = child.tree

        return tree

    @property
    def as_dict(self) -> dict[str, int | bool | None]:
        return {
            "offset": self.offset,
            "size": self.size,
            "zipped": self.zipped,
            "created": self.created,
            "updated": self.updated
        }
