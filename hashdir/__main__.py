#!/usr/bin/env python3
import logging
import sys
import traceback
from typing import List

from . import cli, generate_summary, hash_paths, logging_config

EXIT_CODE_ERROR = 127


def run(args: List[str]) -> None:
    logger = logging_config.setup_logger()

    args = cli.parse_args(args)
    if not args:
        return

    logger.setLevel(args.log_level)

    result = hash_paths(args.directory_or_file, args.algorithm, args.exclude)

    if not args.quiet:
        print(generate_summary(result.entries), end="")
    print(result.aggregate_hash)


def main() -> None:
    args = sys.argv[1:]
    exit_code = 0
    try:
        run(args)
    except KeyboardInterrupt:
        logging.error("Terminated on user input.")
        exit_code = EXIT_CODE_ERROR
    except Exception as e:
        logging.error(
            "An unknown error has occurred: %s"
            ". Use '--log-level debug' to see details.",
            e,
        )
        logging.debug(traceback.format_exc())
        exit_code = EXIT_CODE_ERROR
    sys.stdout.flush()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
