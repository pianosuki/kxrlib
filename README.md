# Kxrlib

Kxrlib is a Python library designed to streamline modding for the MMORPG [Onigiri](http://onigiri.cyberstep.jp). 

## Features
- Packing a .kxr file from a source directory
- Unpacking a .kxr file to an output directory (Currently missing filenames and directory structures)

## Planned Features
- Implement fuzzy matching algorithms to restore filenames and directory structures for unpacked .kxr files
  - The goal is achieve to universal compatibility with any version of the game files without relying on having the correct pkg.json
- Create a transcompiler to facilitate scripting accessibility for modding the game

## Installation
```bash
git clone https://github.com/pianosuki/kxrlib.git
cd kxrlib
```

## Usage (Utility)
```bash
> python main.py {pack,unpack} ...

# Packing a .kxr
# Outputs to parent directory
> python main.py pack path/to/source/directory

# Unpacking a .kxr
# Outputs to parent directory
> python main.py unpack /path/to/file.kxr

# Specify an output
> python main.py pack path/to/source/directory -o path/to/output.kxr
> python main.py unpack /path/to/file.kxr -o path/to/output/directory

# View help message
> python main.py -h

# Logs are saved to logs/pack_kxr.log and logs/unpack_kxr.log
```

## Usage (Library)
```python
from kxrlib import KxrFile

kxr_file = KxrFile("path/to/file.kxr")

async with kxr_file.open("rb"):
  # KXR is automatically processed and its header entries are accessible via kxr_file.root
  print(kxr_file.header_summary)
  print(kxr_file.root.tree)

# Other useful classes that are semi-faithful implementations of the ones in onigiri's source code:

# Metadata for folders, files, names, offsets and sizes of content in the actual KXR body
from kxrlib import KxrHeaderEntry

# Contains the symmetric crypt method used on onigiri's game files (Credit to HikikoMarmy)
from kxrlib import ByteBuffer

# VFS classes used by onigiri as an in-memory storage for loaded game files
from kxrlib import KResourceDir, KResourceFile

# More to come!
```

## Contributing
Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
