import hashlib
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


def hash_file_md5(file_path: str) -> str:
    hash_obj = hashlib.md5()
    return hash_file_hashlib(file_path, hash_obj)


def hash_file_sha1(file_path: str) -> str:
    hash_obj = hashlib.sha1()
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
