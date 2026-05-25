from enum import Enum


class HashAlgorithm(Enum):
    """Enumeration of supported hash algorithms."""

    MD5 = "md5"
    SHA1 = "sha1"
    IMOHASH = "imohash"

    def __str__(self) -> str:
        """Return the string representation for argparse choices."""
        return self.value
