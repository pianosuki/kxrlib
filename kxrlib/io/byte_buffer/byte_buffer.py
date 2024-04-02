import zlib
from io import BytesIO

from .data_format import DataFormat
from .reader import reader
from .writer import writer
from .types import DataType

MODULO = 2**32
MASK = MODULO - 1


class ByteBuffer:

    def __init__(self, capacity: int = -1):
        self._capacity = capacity
        self._buffer = BytesIO()

    def __len__(self) -> int:
        return len(self._buffer.getbuffer())

    def __bool__(self) -> bool:
        return bool(self._buffer.getbuffer())

    @reader
    def _read(self, size: int) -> DataType:
        if self.capacity != -1 and self.pos + size > self.capacity:
            raise BufferError("Reading the data would cause a buffer overflow")

        return self._buffer.read(size)

    @writer
    def _write(self, data: bytes):
        if self.capacity != -1 and self.pos + len(data) > self.capacity:
            raise BufferError("Writing the data would cause a buffer overflow")

        self._buffer.write(data)

    def get(self, data_format: DataFormat | str) -> DataType:
        if not isinstance(data_format, DataFormat) and not isinstance(data_format, str):
            raise TypeError(f"Argument 'data_format' must be one of {(DataFormat, str)}, not {type(data_format)}")
        if isinstance(data_format, str) and data_format not in DataFormat.chars():
            raise ValueError(f"Argument 'data_format' as {str} must be one of {DataFormat.chars()}, not '{data_format}'")

        if isinstance(data_format, str):
            data_format = DataFormat(data_format)

        return self._read(data_format)

    def put(self, data_format: DataFormat | str, data: DataType):
        if not isinstance(data_format, DataFormat) and not isinstance(data_format, str):
            raise TypeError(f"Argument 'data_format' must be one of {(DataFormat, str)}, not {type(data_format)}")
        if isinstance(data_format, str) and data_format not in DataFormat.chars():
            raise ValueError(f"Argument 'data_format' as {str} must be one of {DataFormat.chars()}, not '{data_format}'")
        if not isinstance(data, DataType):
            raise TypeError(f"Argument 'data' must be {DataType}, not {type(data)}")

        if isinstance(data_format, str):
            data_format = DataFormat(data_format)

        self._write(data_format, data)

    def crypt(self, magic: int):
        data_array = bytearray(self.buffer)
        i = 0

        while i < len(data_array):
            if (i % 4 == 0) and (i > 0):
                magic = ((magic * 2) & MASK) | (((~((magic >> 3) ^ magic)) & MASK) >> 0x0D) & 1

            if (i + 4) < len(data_array):
                data_segment = int.from_bytes(data_array[i:i + 4], byteorder="little")
                data_segment ^= magic

                data_array[i:i + 4] = data_segment.to_bytes(4, byteorder="little")
                i += 4
            else:
                magic_mod = magic >> (8 * (i % 4)) & 0xFF

                single_byte = data_array[i]
                single_byte ^= magic_mod

                data_array[i] = single_byte
                i += 1

        self.buffer = bytes(data_array)

    def compress(self, level: int = 5):
        try:
            self.buffer = zlib.compress(self.buffer, level=level)
        except zlib.error as e:
            raise RuntimeError(str(e))

    def decompress(self):
        try:
            self.buffer = zlib.decompress(self.buffer, bufsize=10240)
        except zlib.error as e:
            raise RuntimeError(str(e))

    @property
    def pos(self) -> int:
        return self._buffer.tell()

    @pos.setter
    def pos(self, offset: int):
        self._buffer.seek(offset)

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def size(self) -> int:
        return len(self)

    @property
    def buffer(self) -> bytes:
        return self._buffer.getvalue()

    @buffer.setter
    def buffer(self, data: bytes):
        if not isinstance(data, bytes):
            raise TypeError(f"Argument 'data' must be {bytes}, not {type(data)}")
        if len(data) > self._capacity > 0:
            raise ValueError("Size of argument 'data' exceeds buffer capacity")

        self._buffer = BytesIO(data)

    @classmethod
    def from_bytes(cls, data: bytes, size: int = -1) -> "ByteBuffer":
        bbuf = cls(size)
        bbuf.buffer = data
        return bbuf
