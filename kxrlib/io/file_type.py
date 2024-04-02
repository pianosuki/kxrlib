from __future__ import annotations

from enum import Enum
from dataclasses import dataclass


@dataclass
class FileCriteria:
    needs_zipping: bool


class FileType(Enum):
    KMD = "kmd", FileCriteria(needs_zipping=True)
    KMDA = "kmda", FileCriteria(needs_zipping=True)
    KSP = "ksp", FileCriteria(needs_zipping=True)
    TXT = "txt", FileCriteria(needs_zipping=True)
    HTM = "htm", FileCriteria(needs_zipping=True)
    HTML = "html", FileCriteria(needs_zipping=True)
    NUT = "nut", FileCriteria(needs_zipping=True)
    PTC = "ptc", FileCriteria(needs_zipping=True)
    SCM = "scm", FileCriteria(needs_zipping=True)
    MAT = "mat", FileCriteria(needs_zipping=True)
    KGI = "kgi", FileCriteria(needs_zipping=True)
    DDS = "dds", FileCriteria(needs_zipping=True)
    PNG = "png", FileCriteria(needs_zipping=False)
    JPG = "jpg", FileCriteria(needs_zipping=False)
    JPEG = "jpeg", FileCriteria(needs_zipping=False)
    PVR = "pvr", FileCriteria(needs_zipping=True)
    AIF = "aif", FileCriteria(needs_zipping=True)
    AIFF = "aiff", FileCriteria(needs_zipping=True)
    KMA = "kma", FileCriteria(needs_zipping=False)
    OGG = "ogg", FileCriteria(needs_zipping=False)
    WAV = "wav", FileCriteria(needs_zipping=False)
    FX = "fx", FileCriteria(needs_zipping=True)
    MOT = "mot", FileCriteria(needs_zipping=True)
    MXT = "mxt", FileCriteria(needs_zipping=True)
    PT2 = "pt2", FileCriteria(needs_zipping=True)
    UNKNOWN = "", FileCriteria(needs_zipping=True)

    def __init__(self, extension: str, file_criteria: FileCriteria | None = None):
        self._value_ = extension
        self.criteria = file_criteria

    @classmethod
    def from_extension(cls, extension: str) -> FileType:
        for name, member in cls.__members__.items():
            if name.lower() == extension.lower():
                return member

        return FileType.UNKNOWN
