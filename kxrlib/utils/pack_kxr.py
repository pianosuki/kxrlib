import os
import re
import asyncio

from kxrlib.logger_setup import logger_setup
from kxrlib.console import get_yes_no_input, generate_progress_bar, generate_begin_end_blocks, format_time
from kxrlib.io import KxrFile, KFile, KxrHeaderEntry, KResource, KResourceFile, KResourceDir
from kxrlib.io.kxr_file import KXR_NAME

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

    print(resource_dir.generate_resource_summary_block())

    if not get_yes_no_input(f"Packing to: '{kxr_file.path}'\nProceed?{' (Overwrite existing file)' if kxr_file.exists else ''}", "y"):
        return

    if kxr_file.exists:
        await kxr_file.delete()

    kxr_packer = KxrPacker(kxr_file, resource_dir)
    await kxr_packer.pack()

    print("\nDone!")


class KxrPacker:
    def __init__(self, kxr_file: KxrFile, resource_dir: KResourceDir):
        self.kxr_file = kxr_file
        self.resource_dir = resource_dir

        self.resource_summary = self.resource_dir.resource_summary
        self.progress_generator = ((i + 1) / self.total_files for i in range(self.total_files))

        self.start_time: float | None = None
        self.data_packed: int = 0

    async def pack(self):
        if self.kxr_file.exists:
            raise FileExistsError(f"Kxr file already exists: {self.kxr_file.path}")

        async with self.kxr_file.open("w+b"):
            resource_summary_block_lines = self.resource_dir.generate_resource_summary_block(self.resource_summary).split("\n")

            begin_block_lines, end_block_lines = [block.split("\n") for block in generate_begin_end_blocks("PACK", len(max(resource_summary_block_lines, key=len)))]

            for line in begin_block_lines:
                logger.info(line)

            for line in resource_summary_block_lines:
                logger.info(line)

            logger.info(f"Input: {self.resource_dir}")
            logger.info(f"Output: \"{self.kxr_file.path}\"")

            self.start_time = asyncio.get_running_loop().time()

            self.kxr_file.root.populate(self.resource_dir)

            await self._recursive_pack(self.resource_dir, self.kxr_file.root)

            formatted_elapsed_time = format_time(asyncio.get_running_loop().time() - self.start_time)
            logger.info(f"Time elapsed: {formatted_elapsed_time}")

            for line in end_block_lines:
                logger.info(line)

    async def _recursive_pack(self, resource_dir: KResourceDir, entry: KxrHeaderEntry):
        for child in resource_dir.children.values():
            await self._process_resource(child, entry)

    async def _process_resource(self, resource: KResource, entry: KxrHeaderEntry):
        if isinstance(resource, KResourceFile):
            await self._pack_file(resource, entry)
        elif isinstance(resource, KResourceDir):
            await self._recursive_pack(resource, entry.children[resource.name])

        logger.info(
            f"Processed \"{resource.path}\": "
            f"offset={self.kxr_file.datasize - resource.packed_size if isinstance(resource, KResourceFile) else None} "
            f"size={resource.packed_size} "
            f"zipped={resource.needs_zipping}"
        )

    async def _pack_file(self, resource_file: KResourceFile, entry: KxrHeaderEntry):
        self._update_progress(next(self.progress_generator))

        bbuf = await resource_file.read()

        await entry.put_content(resource_file.name, bbuf, resource_file.type.criteria.needs_zipping)

        resource_file.packed_size = bbuf.size
        self.data_packed += bbuf.size

    def _update_progress(self, current: float):
        if current * self.total_files == 1:
            print()

        megabytes = self.data_packed / (1024 ** 2)

        formatted_elapsed_time = format_time(asyncio.get_running_loop().time() - self.start_time)

        bar = generate_progress_bar(current)

        progress_string = (
            f"\rPacking file: ({int(current * self.total_files)}/{self.total_files}) | "
            f"Data packed: {megabytes:.2f}MB | "
            f"Time elapsed: {formatted_elapsed_time} | "
            f"{bar} {round(current * 100, 2)}%"
        )

        print(progress_string, end="", flush=True)

        if current * self.total_files == self.total_files:
            print()

    @property
    def total_files(self) -> int:
        return self.resource_summary["num_files"]
