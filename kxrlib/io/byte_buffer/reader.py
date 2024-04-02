from __future__ import annotations

from struct import unpack
from typing import TYPE_CHECKING, Callable
from functools import wraps

from .data_format import DataFormat
from .types import DataType

if TYPE_CHECKING:
    from .byte_buffer import ByteBuffer


class Reader:
    def __init__(self, bbuf: ByteBuffer, data_format: DataFormat, _read: Callable[[ByteBuffer, int], DataType]):
        self._reader = self._get_reader(data_format)
        self._read_from_bbuf: Callable[[int], DataType] = lambda size: _read(bbuf, size)

    def read(self) -> DataType:
        return self._reader()

    def _get_reader(self, data_format: DataFormat) -> Callable[[], DataType]:
        if not isinstance(data_format, DataFormat):
            raise TypeError(f"Argument 'data_format' must be {DataFormat}, not {type(data_format)}")

        match data_format:
            case DataFormat.INT:
                return self._read_int
            case DataFormat.SHORT:
                return self._read_short
            case DataFormat.BYTE:
                return self._read_byte
            case DataFormat.HALF:
                return self._read_half
            case DataFormat.FLOAT:
                return self._read_float
            case DataFormat.DOUBLE:
                return self._read_double
            case DataFormat.STRING:
                return self._read_string
            case DataFormat.PACKED:
                return self._read_packed

    def _read_int(self) -> int:
        fmt = ">i"
        data = self._read_from_bbuf(4)
        return unpack(fmt, data)[0]

    def _read_short(self) -> int:
        fmt = ">h"
        data = self._read_from_bbuf(2)
        return unpack(fmt, data)[0]

    def _read_byte(self) -> bytes:
        fmt = ">c"
        data = self._read_from_bbuf(1)
        return unpack(fmt, data)[0]

    def _read_half(self) -> float:
        fmt = ">e"
        data = self._read_from_bbuf(2)
        return unpack(fmt, data)[0]

    def _read_float(self) -> float:
        fmt = ">f"
        data = self._read_from_bbuf(4)
        return unpack(fmt, data)[0]

    def _read_double(self) -> float:
        fmt = ">d"
        data = self._read_from_bbuf(8)
        return unpack(fmt, data)[0]

    def _read_string(self) -> str:
        fmt = "{}s"
        length = int.from_bytes(self._read_from_bbuf(2))
        data = self._read_from_bbuf(length)
        return unpack(fmt.format(length), data)[0].decode()

    def _read_packed(self) -> ...:
        raise NotImplementedError


def reader(_read: Callable[[ByteBuffer, int], DataType]) -> Callable:

    @wraps(_read)
    def wrapper(bbuf: ByteBuffer, data_format: DataFormat) -> DataType:
        reader_ = Reader(bbuf, data_format, _read)
        return reader_.read()

    return wrapper
