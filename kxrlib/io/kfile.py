import os
import asyncio
from io import FileIO

from .byte_buffer import ByteBuffer
from .open_mode import OpenMode
from .opener_ctx import OpenerContextManager

DEFAULT_OPEN_MODE = OpenMode.READ_BINARY


class KFile:
    def __init__(self, path: str):
        if not isinstance(path, str):
            raise TypeError(f"Argument 'path' must be {str}, not {type(path)}")

        self._path = path
        self._mode: str | None = None
        self._io: FileIO | None = None
        self._lock = asyncio.Lock()

    def open(self, mode: str | OpenMode = DEFAULT_OPEN_MODE) -> OpenerContextManager:
        return OpenerContextManager(self._open(mode), self.close)

    async def _open(self, mode: str | OpenMode):
        if isinstance(self._io, FileIO) and not self._io.closed:
            raise PermissionError(f"KFile is already opened: {self}")

        async with self._lock:
            self.mode = mode

            self._io = FileIO(self.path, str(self.mode))

    async def close(self):
        if not self.opened:
            return

        async with self._lock:
            self._io.close()
            self._io = None

    async def read(self, size: int = -1) -> ByteBuffer:
        if not self.opened:
            raise PermissionError("KFile must be opened to read from it")

        async with self._lock:
            data = self._io.read(size)

            return ByteBuffer.from_bytes(data)

    async def write(self, bbuf: ByteBuffer):
        if not self.opened:
            raise PermissionError("KFile must be opened to write to it")

        async with self._lock:
            self._io.write(bbuf.buffer)

    def seek(self, offset: int):
        self._io.seek(offset)

    def makedirs(self):
        os.makedirs(self.path, exist_ok=True)

    async def delete(self):  # USE WITH CAUTION
        async with self._lock:
            if not self.is_dir:
                os.remove(self.path)
            else:
                for root, folders, files in os.walk(self.path, topdown=False):
                    for file in files:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)

                    for folder in folders:
                        dir_path = os.path.join(root, folder)
                        os.rmdir(dir_path)

                os.rmdir(self.path)

    @property
    def path(self) -> str:
        return self._path

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def dirname(self) -> str:
        return os.path.dirname(self.path)

    @property
    def extension(self) -> str | None:
        extension = os.path.splitext(self.path)[1]

        if extension:
            return extension.lstrip(".")
        else:
            return None

    @property
    def mode(self) -> OpenMode | None:
        return self._mode

    @mode.setter
    def mode(self, mode: str | OpenMode):
        if not isinstance(mode, str) and not isinstance(mode, OpenMode):
            raise TypeError(f"Argument 'mode' must be one of {(str, OpenMode)}, not {type(mode)}")
        if self.opened:
            raise PermissionError("Cannot change mode while KFile is opened")

        if isinstance(mode, str):
            try:
                self._mode = OpenMode(mode)
            except ValueError:
                raise
        else:
            self._mode = mode

    @property
    def exists(self) -> bool:
        return os.path.exists(self.path)

    @property
    def is_dir(self) -> bool:
        return os.path.isdir(self.path)

    @property
    def locked(self) -> bool:
        return self._lock.locked()

    @property
    def opened(self):
        return isinstance(self._io, FileIO) and not self._io.closed
