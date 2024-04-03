import os
import asyncio

from kxrlib.logger import logger_setup
from kxrlib.console import get_yes_no_input
from kxrlib import KxrFile, KFile, KxrUnpacker

logger = logger_setup(__name__)


def unpack_kxr(kxr_path: str, output_path: str | None = None):
    if not isinstance(kxr_path, str):
        raise TypeError(f"Argument 'kxr_file' must be {str}, not {type(kxr_path)}")
    if not isinstance(output_path, str) and output_path is not None:
        raise TypeError(f"Argument 'output_path' must be {str}, not {type(output_path)}")

    kxr_path = os.path.abspath(kxr_path)

    if not os.path.exists(kxr_path):
        raise FileNotFoundError(f"File not found: '{kxr_path}'")
    if not os.path.isfile(kxr_path):
        raise IsADirectoryError(f"Kxr file must not be a directory: '{kxr_path}'")

    if output_path:
        output_path = os.path.abspath(output_path)

    asyncio.run(_unpack_kxr(kxr_path, output_path))


async def _unpack_kxr(kxr_path: str, output_path: str | None = None):
    kxr_file = KxrFile(kxr_path)

    async with kxr_file.open():
        if kxr_file.root.name:
            kxr_name = kxr_file.root.name
        else:
            kxr_name = kxr_file.matched_name

    if not output_path:
        output_path = os.path.join(os.path.dirname(kxr_path), kxr_name)

    output_dir = KFile(output_path)

    kxr_unpacker = KxrUnpacker(kxr_file, output_dir, logger=logger)

    print(kxr_file.generate_header_summary_block(kxr_unpacker.header_summary))

    if not get_yes_no_input(f"Unpacking to: '{output_dir.path}'\nProceed?", "y"):
        return

    await kxr_unpacker.unpack()

    print("\nDone!")
