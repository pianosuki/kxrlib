import asyncio
import re

from kxrlib.console import generate_statistics_block
from .byte_buffer import ByteBuffer
from .kfile import KFile
from .kxr_header_entry import KxrHeaderEntry, EntryType
from .open_mode import OpenMode
from .opener_ctx import OpenerContextManager

DEFAULT_OPEN_MODE = OpenMode.READ_BINARY

KXR_NAME = r"^([a-zA-Z0-9_]+?)(?:-\w{4})?\.kxr$"


class KxrFile:
    """
    [Kxr file format]
     - 0 to 3:                  "kxrf"
     - 4 to 7:                  passhash
     - 8 to 11:                 datasize
     - 12 to 15:                headersize
     - 16 to 47:                stampdata
     - 48 to datasize - 48:     contentdata
     - datasize to headersize:  headerdata
    """

    def __init__(self, file: str | KFile):
        self._kfile = file if isinstance(file, KFile) else KFile(file)

        if self._kfile.is_dir:
            raise IsADirectoryError(f"Kxr file must not be a directory: '{self._kfile.path}'")

        self.root: KxrHeaderEntry | None = None
        self.passhash = 0
        self.datasize = 0
        self.headersize = 0
        self.changed = asyncio.Event()
        self._lock = asyncio.Lock()

    def open(self, mode: str | OpenMode = DEFAULT_OPEN_MODE) -> OpenerContextManager:
        return OpenerContextManager(self._open(mode), self.close)

    async def _open(self, mode: str | OpenMode):
        if self.opened:
            raise PermissionError("Kxr file is already opened")

        if self._kfile.exists:
            await self._kfile.open(mode)
            bbuf = await self._kfile.read(16)

            if not all([bbuf.get("b") == char.encode() for char in "kxrf"]):
                raise ValueError("Invalid Kxr file header")

            self.passhash = bbuf.get("i")
            self.datasize = bbuf.get("i")
            self.headersize = bbuf.get("i")

            self.root = KxrHeaderEntry(self, entry_type=EntryType.ROOT)

            hbbuf = await self.read_from_kxr(self.datasize, self.headersize)
            hbbuf.crypt(self.passhash ^ self.datasize)

            self.root.recursive_read_entries(hbbuf)
        else:
            await self._kfile.open("w+b")

            self.datasize = 48
            self.root = KxrHeaderEntry(self, entry_type=EntryType.ROOT, name=self.matched_name, created=0, updated=0)

            await self.save()

    async def close(self):
        if not self.opened:
            return

        if self.changed.is_set() and not self.is_readonly:
            await self.save()

        await self._kfile.close()

    async def read_from_kxr(self, offset: int, size: int) -> ByteBuffer:
        if not self.opened:
            raise PermissionError("Kxr file must be opened to read from it")

        async with self._lock:
            self._kfile.seek(offset)

            return await self._kfile.read(size)

    async def write_to_kxr(self, offset: int, bbuf: ByteBuffer):
        if not self.opened:
            raise PermissionError("Kxr file must be opened to write to it")

        async with self._lock:
            self._kfile.seek(offset)

            await self._kfile.write(bbuf)

            self.changed.set()

    async def save(self):
        bbuf = ByteBuffer()
        hbbuf = ByteBuffer()

        for char in "kxrf":
            bbuf.put("b", char.encode())
        bbuf.put("i", self.passhash)
        bbuf.put("i", self.datasize)

        self.root.recursive_write_entries(hbbuf)

        hbbuf.crypt(self.passhash ^ self.datasize)
        self.headersize = hbbuf.size

        bbuf.put("i", self.headersize)

        await self.write_to_kxr(0, bbuf)
        await self.write_to_kxr(self.datasize, hbbuf)

        self.changed.clear()

    def generate_header_summary_block(self, summary: dict[str, int] | None = None) -> str:
        summary = summary if summary is not None else self.header_summary

        title = "KXR SUMMARY"

        desc_strings = [
            "Kxr file",
            "Folders",
            "Total files",
            "Zipped files"
        ]

        value_strings = [
            self.name,
            *[str(item) for item in summary.values()]
        ]

        return generate_statistics_block(title, desc_strings, value_strings)

    async def delete(self):
        async with self._lock:
            await self._kfile.delete()

    @property
    def path(self) -> str:
        return self._kfile.path

    @property
    def name(self) -> str:
        return self._kfile.name

    @property
    def mode(self) -> OpenMode | None:
        return self._kfile.mode

    @property
    def exists(self) -> bool:
        return self._kfile.exists

    @property
    def is_readonly(self) -> bool:
        return self.mode is OpenMode.READ_BINARY

    @property
    def opened(self) -> bool:
        return self._kfile.opened

    @property
    def matched_name(self) -> str:
        kxr_name_match = re.match(KXR_NAME, self.name)

        if not kxr_name_match:
            raise ValueError(f"Could not match a name for the Kxr file's filename: '{self.name}'")

        return kxr_name_match.group(1)

    @property
    def header_tree(self) -> dict[str, KxrHeaderEntry | dict]:
        if self.root is None:
            raise ValueError(f"No root header entry is assigned to Kxr file yet: {self}")

        return self.root.tree

    @property
    def header_summary(self) -> dict[str, int]:

        def accumulate_stats(tree: dict, running_stats: dict[str, int]):
            for value in tree.values():
                if isinstance(value, KxrHeaderEntry):
                    running_stats["num_files"] += 1

                    if value.zipped:
                        running_stats["num_zipped_files"] += 1
                elif isinstance(value, dict):
                    running_stats["num_folders"] += 1

                    accumulate_stats(value, running_stats)

        header_tree = self.header_tree
        stats = {
            "num_folders": 0,
            "num_files": 0,
            "num_zipped_files": 0
        }

        accumulate_stats(header_tree, stats)

        return stats
