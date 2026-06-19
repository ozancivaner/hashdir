import argparse
import importlib.metadata
from typing import List, Optional

from .algorithms import HashAlgorithm

NAME = "hashdir"
DESCRIPTION = (
    "A command line tool to calculate hashes of directory trees "
    "using various hash algorithms."
)


def get_version() -> str:
    try:
        return importlib.metadata.version(NAME)
    except importlib.metadata.PackageNotFoundError:
        return "development"


def get_parser() -> argparse.ArgumentParser:
    version = get_version()
    parser = argparse.ArgumentParser(prog=NAME, description=DESCRIPTION)

    parser.add_argument(
        "directory_or_file",
        nargs="*",
        default=["."],
        help="directories or files to hash",
    )

    parser.add_argument(
        "-a",
        "--algorithm",
        type=HashAlgorithm,
        choices=list(HashAlgorithm),
        default=HashAlgorithm.MD5,
        help="the hashing algorithm for files. 'imohash' is optional and provides"
        " constant-time hashing for large files, but produces approximate results."
        " See documentation for installation.",
    )

    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="exclude a pattern, like .git/* or *.log",
    )

    parser.add_argument(
        "--log-level",
        type=str.upper,
        choices=["DEBUG", "INFO", "ERROR"],
        default="INFO",
        help="set the logging level.",
        metavar="{debug,info,error}",
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="only output the final hash value."
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"{NAME} {version}"
    )

    return parser


def parse_args(args: Optional[List[str]]) -> argparse.Namespace:
    argument_parser = get_parser()
    return argument_parser.parse_args(args)
