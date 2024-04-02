import argparse

from kxrlib import pack_kxr, unpack_kxr


def main():
    parser = argparse.ArgumentParser(
        description="Utility to pack and unpack .kxr files",
        epilog="https://github.com/pianosuki/kxrlib"
    )

    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    pack_parser = subparsers.add_parser("pack", help="Pack a KXR from a source directory")
    pack_parser.add_argument("source_dir", type=str, help="Source directory to pack")
    pack_parser.add_argument("-o", "--output", help="Destination KXR to create")

    unpack_parser = subparsers.add_parser("unpack", help="Unpack a KXR to an output directory")
    unpack_parser.add_argument("source_kxr", type=str, help="Source KXR to unpack")
    unpack_parser.add_argument("-o", "--output", help="Destination directory to unpack to")

    args = parser.parse_args()

    match args.command:
        case "pack":
            pack_kxr(args.source_dir, args.output)

        case "unpack":
            unpack_kxr(args.source_kxr, args.output)


if __name__ == "__main__":
    main()
