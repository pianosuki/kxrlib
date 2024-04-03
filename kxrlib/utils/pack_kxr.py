import os
import re
import asyncio

from kxrlib.logger import logger_setup
from kxrlib.console import get_yes_no_input
from kxrlib.io import KxrFile, KFile, KResourceDir
from kxrlib.io.kxr_file import KXR_NAME
from kxrlib.packaging import KxrPacker

logger = logger_setup(__name__)


def pack_kxr(src_path: str, output_path: str | None = None):
    if not isinstance(src_path, str):
        raise TypeError(f"Argument 'kxr_file' must be {str}, not {type(src_path)}")
    if not isinstance(output_path, str) and output_path is not None:
        raise TypeError(f"Argument 'output_path' must be {str}, not {type(output_path)}")

    src_path = os.path.abspath(src_path)

    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Directory not found: '{src_path}'")
    if not os.path.isdir(src_path):
        raise NotADirectoryError(f"Source directory must be a directory: '{src_path}'")

    if output_path:
        output_path = os.path.abspath(output_path)

        if os.path.isdir(output_path):
            raise IsADirectoryError(f"Output path must not be a directory: '{output_path}'")
        if not re.search(KXR_NAME, os.path.basename(output_path)):
            raise ValueError(f"Output file is not a valid KXR filename: '{os.path.basename(output_path)}'")

    asyncio.run(_pack_kxr(src_path, output_path))


async def _pack_kxr(src_path: str, output_path: str | None = None):
    src_dir = KFile(src_path)

    if not output_path:
        output_path = os.path.join(src_dir.dirname, src_dir.name + ".kxr")

    kxr_file = KxrFile(output_path)

    resource_dir = KResourceDir.from_dir_recursion(src_dir)

    kxr_packer = KxrPacker(kxr_file, resource_dir, logger=logger)

    print(resource_dir.generate_resource_summary_block())

    if not get_yes_no_input(f"Packing to: '{kxr_file.path}'\nProceed?{' (Overwrite existing file)' if kxr_file.exists else ''}", "y"):
        return

    if kxr_file.exists:
        await kxr_file.delete()

    await kxr_packer.pack()

    print("\nDone!")
