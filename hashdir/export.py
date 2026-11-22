"""Process with multi-algorithms.

Export data to json file or hashlookup server.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import unicodedata
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterator

from .core import FileEntry, deduplicate_file_entries, get_files_to_hash, prepare_paths

try:
    import pefile  # type: ignore
except ImportError:
    pefile = None

try:
    import ssdeep  # type: ignore
except ImportError:
    ssdeep = None

try:
    import tlsh  # type: ignore
except ImportError:
    tlsh = None

CHUNK_SIZE = 1024 * 1024
SUPPORTED_ALGORITHMS = frozenset({"md5", "sha1", "sha256", "sha512"})
HASH_FIELD_NAMES = {
    "md5": "MD5",
    "sha1": "SHA-1",
    "sha256": "SHA-256",
    "sha512": "SHA-512",
}


def decode_pe_string(value: Any) -> str | None:
    """Safely decode a PE version-resource value."""
    if value is None:
        return None

    if isinstance(value, bytes):
        for encoding in ("utf-8", "utf-16-le", "latin-1"):
            try:
                decoded = value.rstrip(b"\x00").decode(encoding).strip()
            except UnicodeDecodeError:
                continue

            if decoded:
                return decoded

        return None

    decoded = str(value).strip()
    return decoded or None


def _extract_fixed_version(
    fixed_info: Any,
    result: dict[str, str],
) -> None:
    """Extract version numbers from VS_FIXEDFILEINFO."""
    for fixed in fixed_info:
        if "ProductVersion" not in result:
            try:
                result["ProductVersion"] = _version_from_dwords(
                    fixed.ProductVersionMS,
                    fixed.ProductVersionLS,
                )
            except (AttributeError, TypeError):
                pass

        if "FileVersion" not in result:
            try:
                result["FileVersion"] = _version_from_dwords(
                    fixed.FileVersionMS,
                    fixed.FileVersionLS,
                )
            except (AttributeError, TypeError):
                pass


def get_pe_metadata(path: Path) -> dict[str, str]:
    """Extract IMPHASH and Windows version-resource metadata."""
    if pefile is None:
        return {}

    pe: Any = None

    try:
        pe = pefile.PE(str(path), fast_load=True)
        result: dict[str, str] = {}

        try:
            imphash = pe.get_imphash()
            if imphash:
                result["IMPHASH"] = imphash.upper()
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # nosec B110

        try:
            pe.parse_data_directories(
                directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # nosec B110

        file_info = getattr(pe, "FileInfo", None)
        if file_info:
            _extract_version_strings(file_info, result)

        fixed_info = getattr(pe, "VS_FIXEDFILEINFO", None)
        if fixed_info:
            _extract_fixed_version(fixed_info, result)

        return result

    except Exception:  # pylint: disable=broad-exception-caught
        return {}

    finally:
        if pe is not None:
            try:
                pe.close()
            except Exception:  # pylint: disable=broad-exception-caught
                pass  # nosec B110


def _extract_version_strings(
    file_info: Any,
    result: dict[str, str],
) -> None:
    """Extract StringFileInfo values from a PE."""
    for info_group in file_info:
        groups = info_group if isinstance(info_group, list) else [info_group]

        for info in groups:
            string_tables = getattr(info, "StringTable", [])

            for string_table in string_tables:
                entries = getattr(string_table, "entries", {})

                for key, value in entries.items():
                    decoded_key = decode_pe_string(key)
                    decoded_value = decode_pe_string(value)

                    if not decoded_key or not decoded_value:
                        continue

                    key_name = decoded_key.lower()

                    if key_name == "productname":
                        result["ProductName"] = decoded_value
                    elif key_name in {"companyname", "manufacturer"}:
                        result["CompanyName"] = decoded_value
                    elif key_name == "productversion":
                        result["ProductVersion"] = decoded_value
                    elif key_name == "fileversion":
                        result["FileVersion"] = decoded_value


def _version_from_dwords(high: int, low: int) -> str:
    """Convert Windows version DWORD pairs to a dotted version."""
    return f"{high >> 16}.{high & 0xFFFF}.{low >> 16}.{low & 0xFFFF}"


# pylint: disable=R0912
def calculate_hashes(  # noqa: PLR0912
    path: Path,
    algorithms: list[str],
    calculate_ssdeep: bool = False,
    calculate_tlsh: bool = False,
) -> dict[str, str]:
    """Calculate multiple cryptographic and fuzzy hashes for one file."""
    hashers = {algorithm: hashlib.new(algorithm) for algorithm in algorithms}

    crc32 = 0
    tlsh_hasher: Any = None

    if calculate_tlsh and tlsh is not None:
        try:
            tlsh_hasher = tlsh.Tlsh()
        except Exception:  # pylint: disable=broad-exception-caught
            tlsh_hasher = None

    file_size = path.stat().st_size

    with path.open("rb") as file_handle:
        while True:
            chunk = file_handle.read(CHUNK_SIZE)

            if not chunk:
                break

            for hasher in hashers.values():
                hasher.update(chunk)

            crc32 = zlib.crc32(chunk, crc32)

            if tlsh_hasher is not None:
                try:
                    tlsh_hasher.update(chunk)
                except Exception:  # pylint: disable=broad-exception-caught
                    tlsh_hasher = None

    record = {
        "FileName": path.name,
        "FileSize": str(file_size),
        "CRC32": f"{crc32 & 0xFFFFFFFF:08X}",
    }

    for algorithm, hasher in hashers.items():
        record[HASH_FIELD_NAMES[algorithm]] = hasher.hexdigest().upper()

    if calculate_ssdeep and ssdeep is not None:
        try:
            fuzzy_hash = ssdeep.hash(str(path))
            if fuzzy_hash and fuzzy_hash != "3::":
                record["SSDEEP"] = fuzzy_hash
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # nosec B110

    if calculate_tlsh and tlsh_hasher is not None:
        try:
            tlsh_hasher.final()
            fuzzy_hash = tlsh_hasher.hexdigest()

            if fuzzy_hash and fuzzy_hash.upper() != "TNULL":
                record["TLSH"] = fuzzy_hash.upper()
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # nosec B110

    return record


# pylint: disable=R0913,R0917
def process_file(  # noqa: PLR0913,PLR0917
    path: Path,
    algorithms: list[str],
    calculate_ssdeep: bool,
    calculate_tlsh: bool,
    extract_pe: bool,
    include_path: bool,
) -> tuple[Path, dict[str, str] | None, str | None]:
    """Process one file and return its record or an error."""
    # filesystem_lock seems required to avoid intermittent FileNotFoundError
    # in pytest with more than 1 worker. likely related to pyfakefs
    try:
        record = calculate_hashes(
            path,
            algorithms,
            calculate_ssdeep,
            calculate_tlsh,
        )

        if extract_pe:
            record.update(get_pe_metadata(path))

        if include_path:
            record["ScanPath"] = str(path)

        return path, record, None

    except (OSError, PermissionError) as exc:
        return path, None, f"process_file {type(exc).__name__}: {exc}"

    except Exception as exc:  # pylint: disable=broad-exception-caught
        return path, None, f"process_file2 {type(exc).__name__}: {exc}"


def parse_algorithms(value: str) -> list[str]:
    """Parse and validate the requested hash algorithms."""
    algorithms = [item.strip().lower() for item in value.split(",") if item.strip()]

    invalid = set(algorithms) - SUPPORTED_ALGORITHMS
    if invalid:
        names = ", ".join(sorted(invalid))
        raise ValueError(f"Unsupported algorithms: {names}")

    if not algorithms:
        raise ValueError("At least one hash algorithm is required")

    return algorithms


# pylint: disable=R0913,R0914,R0917
def _run_parallel(  # noqa: PLR0913,PLR0914,PLR0917
    files: Iterator[FileEntry],
    output: Any,
    args: argparse.Namespace,
    algorithms: list[str],
    calculate_ssdeep: bool,
    calculate_tlsh: bool,
    extract_pe: bool,
) -> tuple[int, int, int]:
    """Process files concurrently."""
    futures = []
    scanned = 0
    successful = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for entry in files:
            path = Path(entry.full_path)
            scanned += 1
            futures.append(
                executor.submit(
                    process_file,
                    path,
                    algorithms,
                    calculate_ssdeep,
                    calculate_tlsh,
                    extract_pe,
                    args.include_path,
                )
            )

        for future in futures:
            path, record, error = future.result()

            if error:
                failed += 1
                logging.error("[ERROR] path %s: %s", path, error)
                continue

            if record is not None:
                write_record(output, record)
                successful += 1
    return scanned, successful, failed


def write_record(
    output: Any,
    record: dict[str, str],
) -> None:
    """Write one compact NDJSON record."""
    output.write(
        json.dumps(
            record,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )


# pylint: disable=R0912,R0914,R0915
def run_scan_multi(args: argparse.Namespace) -> int:  # noqa: PLR0912,PLR0914,PLR0915
    """Run the directory scan."""
    paths = [Path(p).expanduser() for p in args.directory_or_file]
    output_path = Path(args.output).expanduser()
    excluded = args.exclude

    errors = []

    for root in paths:
        if not root.exists():
            errors.append(f"ERROR: Path does not exist: {root}")
    if errors:
        logging.error("ERROR:\n%s", "\n".join(errors))
        return 1

    if args.workers < 1:
        logging.error("ERROR: --workers must be >= 1")
        return 1

    try:
        algorithms = parse_algorithms(args.multi_algorithms)
    except ValueError as exc:
        logging.error("ERROR: %s", exc)
        return 1

    calculate_ssdeep = args.ssdeep
    calculate_tlsh = args.tlsh
    extract_pe = args.pe

    if calculate_ssdeep and ssdeep is None:
        logging.warning("WARNING: ssdeep is not installed; SSDEEP omitted.")

    if calculate_tlsh and tlsh is None:
        logging.warning("WARNING: tlsh is not installed; TLSH omitted.")

    if extract_pe and pefile is None:
        logging.warning("WARNING: pefile is not installed; PE metadata omitted.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Scanning: %s", ", ".join(str(p) for p in paths))
    logging.info("Output: %s", output_path)

    scanned = 0
    successful = 0
    failed = 0

    unique_paths = prepare_paths(paths)

    # Normalize exclusion patterns to NFKD for consistent matching regardless of source
    normalized_excluded = [unicodedata.normalize("NFKD", p) for p in excluded]

    files_to_hash = get_files_to_hash(unique_paths, normalized_excluded)

    files_to_hash_deduplicated = deduplicate_file_entries(files_to_hash)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as output:
        if args.workers == 1:
            for entry in files_to_hash_deduplicated:
                path = Path(entry.full_path)
                scanned += 1

                _, record, error = process_file(
                    path,
                    algorithms,
                    calculate_ssdeep,
                    calculate_tlsh,
                    extract_pe,
                    args.include_path,
                )

                if error:
                    failed += 1
                    if not args.quiet:
                        logging.error("Error for path %s: %s", path, error)
                    continue

                if record is not None:
                    write_record(output, record)
                    successful += 1

                if not args.quiet:
                    logging.debug(
                        "Files: %s  Hashed: %s  Errors: %s", scanned, successful, failed
                    )
        else:
            scanned, successful, failed = _run_parallel(
                files_to_hash_deduplicated,
                output,
                args,
                algorithms,
                calculate_ssdeep,
                calculate_tlsh,
                extract_pe,
            )

    if not args.quiet:
        print(file=sys.stderr)

    logging.info("Completed: %s files hashed, %s errors.", successful, failed)

    return 0
