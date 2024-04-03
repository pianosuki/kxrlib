import asyncio
from typing import Generator
from logging import Logger

from kxrlib.logger import NullLogger
from kxrlib import KxrFile, KResourceDir, KxrHeaderEntry, KResource, KResourceFile
from kxrlib.console import generate_begin_end_blocks, format_time, generate_progress_bar


class KxrPacker:
    def __init__(self, kxr_file: KxrFile, resource_dir: KResourceDir, logger: Logger | None = None):
        self.kxr_file = kxr_file
        self.resource_dir = resource_dir
        self.logger = logger if logger is not None else NullLogger()

        self.resource_summary: dict[str, int] = self.resource_dir.resource_summary
        self.progress_generator: Generator[float, None, None] = ((i + 1) / self.total_files for i in range(self.total_files))

        self.start_time: float | None = None
        self.data_packed: int = 0

    async def pack(self):
        if self.kxr_file.exists:
            raise FileExistsError(f"Kxr file already exists: {self.kxr_file.path}")

        async with self.kxr_file.open("w+b"):
            resource_summary_block_lines = self.resource_dir.generate_resource_summary_block(self.resource_summary).split("\n")

            begin_block_lines, end_block_lines = [block.split("\n") for block in generate_begin_end_blocks("PACK", len(max(resource_summary_block_lines, key=len)))]

            for line in begin_block_lines:
                self.logger.info(line)

            for line in resource_summary_block_lines:
                self.logger.info(line)

            self.logger.info(f"Input: {self.resource_dir}")
            self.logger.info(f"Output: \"{self.kxr_file.path}\"")

            self.start_time = asyncio.get_running_loop().time()

            self.kxr_file.root.populate(self.resource_dir)

            await self._recursive_pack(self.resource_dir, self.kxr_file.root)

            formatted_elapsed_time = format_time(asyncio.get_running_loop().time() - self.start_time)
            self.logger.info(f"Time elapsed: {formatted_elapsed_time}")

            for line in end_block_lines:
                self.logger.info(line)

    async def _recursive_pack(self, resource_dir: KResourceDir, entry: KxrHeaderEntry):
        for child in resource_dir.children.values():
            await self._process_resource(child, entry)

    async def _process_resource(self, resource: KResource, entry: KxrHeaderEntry):
        if isinstance(resource, KResourceFile):
            await self._pack_file(resource, entry)
        elif isinstance(resource, KResourceDir):
            await self._recursive_pack(resource, entry.children[resource.name])

        self.logger.info(
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
