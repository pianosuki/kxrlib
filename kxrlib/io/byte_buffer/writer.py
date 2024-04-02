from __future__ import annotations

from struct import pack
from typing import Callable, TYPE_CHECKING
from functools import wraps

from .data_format import DataFormat
from .types import DataType

if TYPE_CHECKING:
    from .byte_buffer import ByteBuffer


class Writer:
    def __init__(self, bbuf: ByteBuffer, data_format: DataFormat, _write: Callable[[ByteBuffer, DataType], None]):
        self._writer = self._get_writer(data_format)
        self._write_to_bbuf: Callable[[DataType], None] = lambda data: _write(bbuf, data)

    def write(self, data: DataType):
        if not isinstance(data, DataType):
            raise TypeError(f"Argument 'data' must be {DataType}, not {type(data)}")

        self._writer(data)

    def _get_writer(self, data_format: DataFormat) -> Callable[[DataType], None]:
        if not isinstance(data_format, DataFormat):
            raise TypeError(f"Argument 'data_format' must be {DataFormat}, not {type(data_format)}")

        match data_format:
            case DataFormat.INT:
                return self._write_int
            case DataFormat.SHORT:
                return self._write_short
            case DataFormat.BYTE:
                return self._write_byte
            case DataFormat.HALF:
                return self._write_half
            case DataFormat.FLOAT:
                return self._write_float
            case DataFormat.DOUBLE:
                return self._write_double
            case DataFormat.STRING:
                return self._write_string
            case DataFormat.PACKED:
                return self._write_packed

    def _write_int(self, data: int):
        fmt = ">i"
        data = pack(fmt, data)
        self._write_to_bbuf(data)

    def _write_short(self, data: int):
        fmt = ">h"
        data = pack(fmt, data)
        self._write_to_bbuf(data)

    def _write_byte(self, data: bytes):
        fmt = ">c"
        data = pack(fmt, data)
        self._write_to_bbuf(data)

    def _write_half(self, data: float):
        fmt = ">e"
        data = pack(fmt, data)
        self._write_to_bbuf(data)

    def _write_float(self, data: float):
        fmt = ">f"
        data = pack(fmt, data)
        self._write_to_bbuf(data)

    def _write_double(self, data: float):
        fmt = ">d"
        data = pack(fmt, data)
        self._write_to_bbuf(data)

    def _write_string(self, data: str):
        fmt = ">h{}s"
        string_length = len(data)
        data = pack(fmt.format(string_length), string_length, data.encode())
        self._write_to_bbuf(data)

    def _write_packed(self, data: ...):
        raise NotImplementedError


def writer(_write: Callable[[ByteBuffer, bytes], None]) -> Callable:

    @wraps(_write)
    def wrapper(bbuf: ByteBuffer, data_format: DataFormat, data: DataType):
        writer_ = Writer(bbuf, data_format, _write)
        writer_.write(data)

    return wrapper
