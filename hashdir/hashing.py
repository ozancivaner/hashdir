import hashlib
from pathlib import Path
from typing import Any

READ_CHUNK_SIZE = 65536  # 64KB


def hash_file_imohash(file_path: str) -> str:
    try:
        import imohash
    except ImportError:
        raise RuntimeError(
            "The 'imohash' library is required for this algorithm but is not"
            " installed. Install it using: pip install 'hashdir[imohash]'"
        ) from None

    return imohash.hashfile(file_path, hexdigest=True)


def hash_file_ssdeep(file_path: str) -> str:
    try:
        import ssdeep
    except ImportError:
        raise RuntimeError(
            "The 'ssdeep' library is required for this algorithm but is not"
            " installed. Install both system package and python module."
        ) from None

    try:
        fuzzy_hash = ssdeep.hash(str(file_path))
        if fuzzy_hash and fuzzy_hash != "3::":
            return fuzzy_hash
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    return ""


def hash_file_tlsh(file_path: str) -> str:
    try:
        import tlsh
    except ImportError:
        raise RuntimeError(
            "The 'tlsh' library is required for this algorithm but is not "
            "installed. Install both the system package and Python module."
        ) from None

    try:
        tlsh_hasher = tlsh.Tlsh()

        with Path(file_path).open("rb") as file_handle:
            while True:
                chunk = file_handle.read(READ_CHUNK_SIZE)

                if not chunk:
                    break

                tlsh_hasher.update(chunk)

        tlsh_hasher.final()
        fuzzy_hash = tlsh_hasher.hexdigest()

        if fuzzy_hash and fuzzy_hash.upper() != "TNULL":
            return fuzzy_hash.upper()

    except (OSError, ValueError):
        pass

    return ""


def hash_file_md5(file_path: str) -> str:
    hash_obj = hashlib.md5()
    return hash_file_hashlib(file_path, hash_obj)


def hash_file_sha1(file_path: str) -> str:
    hash_obj = hashlib.sha1()
    return hash_file_hashlib(file_path, hash_obj)


def hash_file_sha256(file_path: str) -> str:
    hash_obj = hashlib.sha256()
    return hash_file_hashlib(file_path, hash_obj)


def hash_file_sha512(file_path: str) -> str:
    hash_obj = hashlib.sha512()
    return hash_file_hashlib(file_path, hash_obj)


def hash_file_hashlib(file_path: str, hash_obj: Any) -> str:
    with open(file_path, "rb") as f:
        while True:
            buf = f.read(READ_CHUNK_SIZE)
            if not buf:
                break
            hash_obj.update(buf)
    return hash_obj.hexdigest()


def hash_string_sha1(input_str: str) -> str:
    h = hashlib.sha1()
    h.update(input_str.encode())
    return h.hexdigest()
