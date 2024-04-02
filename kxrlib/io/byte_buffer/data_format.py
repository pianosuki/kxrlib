from enum import Enum


class DataFormat(Enum):
    INT = "i"
    SHORT = "s"
    BYTE = "b"
    HALF = "h"
    FLOAT = "f"
    DOUBLE = "d"
    STRING = "t"
    PACKED = "p"

    @classmethod
    def chars(cls) -> list[str]:
        return [member.value for member in cls.__members__.values()]
