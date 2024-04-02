from __future__ import annotations

from kxrlib.io.byte_buffer import ByteBuffer
from kxrlib.io.kfile import KFile
from kxrlib.io.file_type import FileType
from .kresource import KResource


class KResourceFile(KResource):
    def __init__(self, file: str | KFile):
        self._kfile = file if isinstance(file, KFile) else KFile(file)

        if not self._kfile.exists:
            raise FileNotFoundError(f"Argument 'file' must be an existing file: {file}")
        if self._kfile.is_dir:
            raise IsADirectoryError(f"Argument 'file' must not be a directory: {file}")

        super().__init__(self._kfile.name)

        self._type = FileType.from_extension(self._kfile.extension)
        self._packed_size: int | None = None

    async def read(self, size: int = -1) -> ByteBuffer:
        async with self._kfile.open("rb"):
            return await self._kfile.read(size)

    async def write(self, bbuf: ByteBuffer):
        async with self._kfile.open("wb"):
            await self._kfile.write(bbuf)

    @property
    def type(self) -> FileType:
        return self._type

    @property
    def needs_zipping(self) -> bool:
        return self.type.criteria.needs_zipping

    @property
    def packed_size(self) -> int | None:
        return self._packed_size

    @packed_size.setter
    def packed_size(self, size: int):
        if not isinstance(size, int):
            raise TypeError(f"Argument 'size' must be {int}, not {type(size)}")
        if self._packed_size is not None:
            raise PermissionError(f"Cannot change packed size once it has been set")

        self._packed_size = size
