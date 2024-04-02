import os
import asyncio

from kxrlib.logger_setup import logger_setup
from kxrlib.console import get_yes_no_input, generate_progress_bar, generate_begin_end_blocks, format_time
from kxrlib.io import KxrFile, KFile, KxrHeaderEntry

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

    kxr_unpacker = KxrUnpacker(kxr_file, output_dir)

    print(kxr_file.generate_header_summary_block(kxr_unpacker.header_summary))

    if not get_yes_no_input(f"Unpacking to: '{output_dir.path}'\nProceed?", "y"):
        return

    await kxr_unpacker.unpack()

    print("\nDone!")


class KxrUnpacker:
    def __init__(self, kxr_file: KxrFile, output_dir: KFile):
        self.kxr_file = kxr_file
        self.output_dir = output_dir

        self.header_summary = self.kxr_file.header_summary
        self.progress_generator = ((i + 1) / self.total_files for i in range(self.total_files))

        self.start_time: float | None = None
        self.data_unpacked: int = 0

    async def unpack(self):
        async with self.kxr_file.open("rb"):
            self.output_dir.makedirs()

            header_summary_block_lines = self.kxr_file.generate_header_summary_block(self.header_summary).split("\n")

            begin_block_lines, end_block_lines = [block.split("\n") for block in generate_begin_end_blocks("UNPACK", len(max(header_summary_block_lines, key=len)))]

            for line in begin_block_lines:
                logger.info(line)

            for line in header_summary_block_lines:
                logger.info(line)

            logger.info(f"Input: \"{self.kxr_file.path}\"")
            logger.info(f"Output: \"{self.output_dir.path}\"")

            self.start_time = asyncio.get_running_loop().time()

            await self._recursive_unpack(self.kxr_file.root, self.output_dir)

            formatted_elapsed_time = format_time(asyncio.get_running_loop().time() - self.start_time)
            logger.info(f"Time elapsed: {formatted_elapsed_time}")

            for line in end_block_lines:
                logger.info(line)

    async def _recursive_unpack(self, entries: KxrHeaderEntry, output_dir: KFile):
        for child in entries.children.values():
            await self._process_entry(child, output_dir)

    async def _process_entry(self, entry: KxrHeaderEntry, output_dir: KFile):
        if not entry.is_dir:
            await self._unpack_file(entry, output_dir)
        else:
            subdir = KFile(os.path.join(output_dir.path, entry.name))
            subdir.makedirs()

            await self._recursive_unpack(entry, subdir)

        logger.info(
            f"Processed \"{entry.path}\": "
            f"offset={entry.offset} "
            f"size={entry.size} "
            f"unzipped={entry.zipped}"
        )

    async def _unpack_file(self, entry: KxrHeaderEntry, output_dir_: KFile):
        self._update_progress(next(self.progress_generator))

        bbuf = await entry.get_content()

        output_file = KFile(os.path.join(output_dir_.path, entry.name))

        async with output_file.open("wb"):
            await output_file.write(bbuf)

        self.data_unpacked += bbuf.size

    def _update_progress(self, current: float):
        if current * self.total_files == 1:
            print()

        megabytes = self.data_unpacked / (1024 ** 2)

        formatted_elapsed_time = format_time(asyncio.get_running_loop().time() - self.start_time)

        bar = generate_progress_bar(current)

        progress_string = (
            f"\rUnpacking file: ({int(current * self.total_files)}/{self.total_files}) | "
            f"Data unpacked: {megabytes:.2f}MB | "
            f"Time elapsed: {formatted_elapsed_time} | "
            f"{bar} {round(current * 100, 2)}%"
        )

        print(progress_string, end="", flush=True)

        if current * self.total_files == self.total_files:
            print()

    @property
    def total_files(self) -> int:
        return self.header_summary["num_files"]
