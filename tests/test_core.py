import os
import unittest

from hashdir.algorithms import HashAlgorithm
from hashdir.core import (
    hash_paths,
)
from tests.base import HashdirTestCase


class TestCore(HashdirTestCase):
    """Test core hashing functionality."""

    def setUp(self):
        """Initialize the test environment with a known file structure."""
        super().setUp()
        self._create_files_with_known_content()

    def test_hash_directory_md5_no_exclusion(self):
        """Verify directory hashing with MD5 when no exclusions are applied."""
        result = hash_paths([self.test_dir], HashAlgorithm.MD5, [])

        self.assertEqual(
            result.aggregate_hash, "46b75a381149c7e00301c13133e7683c88224fc6"
        )

        # Verify the structure and sorting of the result entries
        self.assertEqual(len(result.entries), 6)

        # Spot-check the first entry (sorted primarily by hash)
        self.assertEqual(result.entries[0].rel_path, "subdir2/fileE.txt")
        self.assertEqual(
            result.entries[0].file_hash, "00958efb88e1841b92055be5b421a795"
        )

    def test_hash_directory_imohash(self):
        """Verify directory hashing with the imohash algorithm."""
        result = hash_paths([self.test_dir], HashAlgorithm.IMOHASH, [])
        EXPECTED_HASH_LENGTH = 32
        self.assertTrue(len(result.entries) > 0)
        self.assertTrue(
            all(len(h.file_hash) == EXPECTED_HASH_LENGTH for h in result.entries)
        )
        self.assertEqual(len(result.aggregate_hash), 40)

    def test_hash_directory_empty_dir(self):
        """Verify that hashing an empty directory returns a valid aggregate hash."""
        empty_dir = "/tmp/empty_dir"
        self.fs.create_dir(empty_dir)

        result = hash_paths([empty_dir], HashAlgorithm.MD5, [])
        self.assertEqual(result.entries, [])
        self.assertEqual(
            result.aggregate_hash, "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        )  # SHA1 of empty string

    def test_hash_paths_order_independence(self):
        """Verify that the aggregate hash is independent of the order of input paths."""
        path_a = os.path.join(self.test_dir, "fileA.txt")
        path_b = os.path.join(self.test_dir, "subdir1")

        # Order 1
        result1 = hash_paths([path_a, path_b], HashAlgorithm.MD5, [])
        # Order 2
        result2 = hash_paths([path_b, path_a], HashAlgorithm.MD5, [])

        self.assertEqual(result1.aggregate_hash, result2.aggregate_hash)

    def test_hash_paths_single_file(self):
        """Verify hashing behavior for a single file path input."""
        path = os.path.join(self.test_dir, "fileA.txt")
        result = hash_paths([path], HashAlgorithm.MD5, [])
        self.assertEqual(len(result.entries), 1)
        self.assertEqual(result.entries[0].rel_path, "fileA.txt")
        self.assertEqual(result.entries[0].root, self.test_dir)


if __name__ == "__main__":
    unittest.main()
