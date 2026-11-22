import argparse
import importlib.metadata
from typing import List, Optional

from .algorithms import HashAlgorithm

NAME = "hashdir"
DESCRIPTION = (
    "A command line tool to calculate hashes of directory trees "
    "using various hash algorithms."
)
EXAMPLES = """Examples
    `hashdir -a md5 hashdir`
    `hashdir -m md5,sha1,sha512 --workers 1 hashdir -o hashes.ndjson`
    `hashdir -m md5,sha1,sha512 --workers 2 --log-level debug  -o hashes.ndjson hashdir`
"""


def get_version() -> str:
    try:
        return importlib.metadata.version(NAME)
    except importlib.metadata.PackageNotFoundError:
        return "development"


def get_parser() -> argparse.ArgumentParser:
    version = get_version()
    parser = argparse.ArgumentParser(
        prog=NAME, description=DESCRIPTION, epilog=EXAMPLES
    )

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

    parser.add_argument(
        "-m",
        "--multi-algorithms",
        default=None,
        help="Comma-separated cryptographic hashes",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="hashes.ndjson",
        help="Output NDJSON file (multi-algorithms only)",
    )
    parser.add_argument(
        "--ssdeep",
        default=False,
        action="store_true",
        help="Enable SSDEEP (multi-algorithms only)",
    )
    parser.add_argument(
        "--tlsh",
        default=False,
        action="store_true",
        help="Enable TLSH (multi-algorithms only)",
    )
    parser.add_argument(
        "--pe",
        action="store_true",
        default=False,
        help="Enable PE metadata and IMPHASH (multi-algorithms only)",
    )
    parser.add_argument(
        "--include-path",
        action="store_true",
        help="Include the local path as ScanPath (multi-algorithms only)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker threads (multi-algorithms only)",
    )

    return parser


def parse_args(args: Optional[List[str]]) -> argparse.Namespace:
    argument_parser = get_parser()
    return argument_parser.parse_args(args)
