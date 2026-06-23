import logging
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Callable, List, Optional

from .algorithms import HashAlgorithm
from .hashing import hash_file_imohash, hash_file_md5, hash_file_sha1, hash_string_sha1


@dataclass(frozen=True)
class FileEntry:
    """Represents a file discovered during directory traversal."""

    root: str
    rel_path: str
    full_path: str


@dataclass(frozen=True)
class HashedFileEntry(FileEntry):
    """Represents a file entry with its calculated hash value."""

    file_hash: str


@dataclass(frozen=True)
class HashdirResult:
    """The result of a directory hashing operation.

    Attributes:
        entries: A list of HashedFileEntry objects, sorted primarily by
            the file hash and secondarily by the relative path. This sorting
            matches the order used to generate the final aggregate hash.
        aggregate_hash: The SHA1 hash of the summary string generated from
            the sorted entries.

    """

    entries: List[HashedFileEntry]
    aggregate_hash: str


def is_excluded(file_path: str, patterns: List[str]) -> bool:
    """Determine if a path should be ignored.

    Checks the path itself and all its ancestor directories against the exclusion
    patterns.
    """
    if not patterns:
        return False

    path_obj = PurePath(file_path)
    # Check the path itself and all its parent directories.
    for part in [path_obj] + list(path_obj.parents):
        if str(part) == ".":
            continue
        for pattern in patterns:
            if part.match(pattern):
                return True
    return False


def prepare_paths(paths: List[str]) -> List[str]:
    """Validate, normalize, and prune input paths for processing.

    This function ensures that all input paths exist, are not symlinks, and are resolved
    to absolute paths. It then sorts them and removes any paths that are redundant
    (e.g., a file inside a directory that is also being processed) to ensure a
    deterministic and efficient file discovery.
    """
    resolved_paths = []
    for p in paths:
        path_obj = Path(p)
        if not path_obj.exists():
            raise ValueError(f"'{p}' is not a valid directory or file.")

        if path_obj.is_symlink():
            raise ValueError(
                f"'{p}' is a symlink. Symlinks are not supported as direct arguments."
            )

        resolved_paths.append(path_obj.resolve())

    # Sorting ensures that parent directories always appear before their children
    resolved_paths.sort()

    pruned = []
    for p in resolved_paths:
        # Check if current path 'p' is a child of any path already in 'pruned'
        if not any(parent == p or parent in p.parents for parent in pruned):
            pruned.append(p)

    return [str(p) for p in pruned]


def _scandir_recursive(
    current_dir_path: str, original_root_path: str, excluded: List[str]
):
    """Recursively scan a directory using os.scandir.

    Yields FileEntry objects for non-excluded files and prunes excluded or symlinked
    directories.
    """
    for entry in os.scandir(current_dir_path):
        # Calculate rel_path relative to the original root path for exclusion checks
        rel_path_raw = os.path.relpath(entry.path, original_root_path)
        # Normalize the relative path to NFKD for consistent internal logic
        # (sorting, exclusion)
        rel_path_normalized = unicodedata.normalize("NFKD", rel_path_raw)
        if entry.is_symlink():
            logging.warning("Ignoring symlink: %s", entry.path)
            continue
        if entry.is_dir(follow_symlinks=False):
            if is_excluded(rel_path_normalized, excluded):
                logging.debug("Excluding directory: %s", rel_path_raw)
                continue
            # Recursively scan non-excluded, non-symlinked directories
            yield from _scandir_recursive(entry.path, original_root_path, excluded)
        elif entry.is_file(follow_symlinks=False):
            if is_excluded(rel_path_normalized, excluded):
                logging.debug("Excluding file: %s", rel_path_raw)
                continue
            yield FileEntry(
                root=original_root_path,
                rel_path=rel_path_normalized,
                full_path=entry.path,
            )


def get_directory_files(path: str, excluded: List[str]):
    """Walk a directory tree using os.scandir.

    Yields FileEntry objects for non-excluded files.
    """
    # The 'path' argument is the root for relative paths in FileEntry
    yield from _scandir_recursive(path, path, excluded)


def deduplicate_file_entries(entries: List[FileEntry]) -> List[FileEntry]:
    """Deduplicate FileEntry objects based on their absolute full_path.

    Sorts by rel_path first to ensure deterministic selection of the relative path if a
    file is found multiple times.

    This provides internal robustness and future-proofing by ensuring the aggregate hash
    remains stable even if input pruning is bypassed or if the underlying file discovery
    logic changes.
    """
    # Sort primarily by rel_path to make the selection deterministic
    sorted_entries = sorted(entries, key=lambda x: x.rel_path)

    seen_full_paths = set()
    for entry in sorted_entries:
        if entry.full_path not in seen_full_paths:
            seen_full_paths.add(entry.full_path)
            yield entry


def get_files_to_hash(paths: List[str], excluded: List[str]) -> List[FileEntry]:
    """Resolve input paths into a flattened list of file entries.

    Produces a list of unique, non-excluded file entries ready for hashing.
    """
    for path_str in paths:
        path = Path(path_str)
        # Existence and symlink checks for root paths are handled in prepare_paths
        if path.is_file():
            # Normalize the file name before exclusion check and FileEntry creation
            file_name_normalized = unicodedata.normalize("NFKD", path.name)
            if not is_excluded(file_name_normalized, excluded):
                yield FileEntry(
                    root=str(path.parent),
                    rel_path=file_name_normalized,
                    full_path=path_str,
                )
        elif path.is_dir():
            yield from get_directory_files(path_str, excluded)


def get_hash_function(algorithm: HashAlgorithm) -> Optional[Callable[[str], str]]:
    if algorithm == HashAlgorithm.MD5:
        return hash_file_md5
    if algorithm == HashAlgorithm.SHA1:
        return hash_file_sha1
    if algorithm == HashAlgorithm.IMOHASH:
        return hash_file_imohash
    return None


def generate_summary(sorted_file_hashes: List[HashedFileEntry]) -> str:
    """Construct a deterministic summary string.

    Uses POSIX-style paths to ensure cross-platform consistency.
    """
    return "".join(
        f"{PurePath(entry.rel_path).as_posix()} {entry.file_hash}\n"
        for entry in sorted_file_hashes
    )


def hash_files(
    algorithm: HashAlgorithm, files_to_hash: List[FileEntry]
) -> List[HashedFileEntry]:
    hash_func = get_hash_function(algorithm)
    if hash_func is None:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    for entry in files_to_hash:
        file_hash = hash_func(entry.full_path)
        yield HashedFileEntry(
            root=entry.root,
            rel_path=entry.rel_path,
            full_path=entry.full_path,
            file_hash=file_hash,
        )


def hash_paths(
    paths: List[str], algorithm: HashAlgorithm, excluded: List[str]
) -> HashdirResult:
    """Execute the full hashing pipeline.

    Includes input normalization, file discovery, individual file hashing, and final
    aggregate hash generation.
    """
    unique_paths = prepare_paths(paths)

    # Normalize exclusion patterns to NFKD for consistent matching regardless of source
    normalized_excluded = [unicodedata.normalize("NFKD", p) for p in excluded]

    files_to_hash = get_files_to_hash(unique_paths, normalized_excluded)

    files_to_hash_deduplicated = deduplicate_file_entries(files_to_hash)

    file_hashes = hash_files(algorithm, files_to_hash_deduplicated)

    # Sort for consistent return value, primarily by hash and then by relative path.
    file_hashes_sorted = sorted(file_hashes, key=lambda x: (x.file_hash, x.rel_path))

    summary = generate_summary(file_hashes_sorted)

    # Regardless of the algorithm selected, the final summary is always
    # hashed using the SHA1 algorithm.
    return HashdirResult(
        entries=file_hashes_sorted, aggregate_hash=hash_string_sha1(summary)
    )
