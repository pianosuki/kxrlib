from __future__ import annotations

import os
from typing import Literal

from kxrlib.console import generate_statistics_block
from kxrlib.io.kfile import KFile
from .kresource import KResource
from .kresource_file import KResourceFile


class KResourceDir(KResource):
    def __init__(self, name: str, children_list: list[KResource] | None = None):
        super().__init__(name)

        self._children: dict[str, KResource] = {}

        if children_list is not None:
            self.children = children_list

    def generate_resource_summary_block(self, summary: dict[str, int] | None = None) -> str:
        summary = summary if summary is not None else self.resource_summary

        title = "KXR SUMMARY"

        desc_strings = [
            "KResource",
            "Folders",
            "Total files",
            "Files to zip"
        ]

        value_strings = [
            self.name,
            *[str(item) for item in summary.values()]
        ]

        return generate_statistics_block(title, desc_strings, value_strings)

    @property
    def children(self) -> dict[str, KResource]:
        return self._children

    @children.setter
    def children(self, children_list: list[KResource]):
        if not isinstance(children_list, list):
            raise TypeError(f"Keyword argument 'children' must be {list}, not {type(children_list)}")
        if not all([isinstance(child, KResource) for child in children_list]):
            raise TypeError(f"Argument 'children_list' must only contain instances of {KResource}")

        self._children.clear()

        for child in children_list:
            self._children[child.name] = child
            child.parent = self

    @property
    def resource_tree(self) -> dict[str, KResourceFile | dict]:
        tree = {}

        for name, child in self.children.items():
            if isinstance(child, KResourceFile):
                tree[name] = child
            elif isinstance(child, KResourceDir):
                tree[name] = child.resource_tree

        return tree

    @property
    def resource_summary(self) -> dict[str, int]:

        def accumulate_stats(tree: dict, running_stats: dict[str, int]):
            for value in tree.values():
                if isinstance(value, KResourceFile):
                    running_stats["num_files"] += 1

                    if value.needs_zipping:
                        running_stats["num_files_need_zipping"] += 1
                elif isinstance(value, dict):
                    running_stats["num_folders"] += 1

                    accumulate_stats(value, running_stats)

        header_tree = self.resource_tree
        stats = {
            "num_folders": 0,
            "num_files": 0,
            "num_files_need_zipping": 0
        }

        accumulate_stats(header_tree, stats)

        return stats

    @property
    def needs_zipping(self) -> Literal[False]:
        return False

    @property
    def packed_size(self) -> int | None:
        total_packed_size = 0

        for child in self.children.values():
            child_packed_size = child.packed_size

            if isinstance(child_packed_size, int):
                total_packed_size += child_packed_size

        return total_packed_size if total_packed_size > 0 else None

    @classmethod
    def from_dir_recursion(cls, src_dir: str | KFile):
        src_dir = src_dir if isinstance(src_dir, KFile) else KFile(src_dir)

        if not src_dir.exists:
            raise FileNotFoundError(f"Argument 'src_dir' must be an existing directory: {src_dir}")
        if not src_dir.is_dir:
            raise NotADirectoryError(f"Argument 'src_dir' must be a directory: {src_dir}")

        children_list = []

        for file in os.listdir(src_dir.path):
            file_path = os.path.join(src_dir.path, file)

            if os.path.isfile(file_path):
                child = KResourceFile(file_path)
            else:
                child = KResourceDir.from_dir_recursion(file_path)

            children_list.append(child)

        return cls(src_dir.name, children_list=children_list)
