from enum import Enum


class OpenMode(Enum):
    READ_BINARY = "rb"
    READ_UPDATE_BINARY = "r+b"
    WRITE_BINARY = "wb"
    WRITE_UPDATE_BINARY = "w+b"

    def __str__(self) -> str:
        return self.value
