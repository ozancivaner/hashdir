"""Test code - hashing."""

# pylint: disable=C0103
import os
import unittest

import pytest

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
            result.aggregate_hash, "ecb1846bae609491964171469afe1ccfa90ea51d"
        )

        # Verify the structure and sorting of the result entries
        self.assertEqual(len(result.entries), 7)

        # Spot-check the first entry (sorted primarily by hash)
        self.assertEqual(result.entries[0].rel_path, "subdir2/fileE.txt")
        self.assertEqual(
            result.entries[0].file_hash, "00958efb88e1841b92055be5b421a795"
        )

    def test_hash_directory_sha256_no_exclusion(self):
        """Verify directory hashing with SHA256 when no exclusions are applied."""
        result = hash_paths([self.test_dir], HashAlgorithm.SHA256, [])

        # Verify the structure and sorting of the result entries
        self.assertEqual(len(result.entries), 7)

        # Spot-check the first entry (sorted primarily by hash)
        self.assertEqual(result.entries[2].rel_path, "subdir2/fileE.txt")
        self.assertEqual(
            result.entries[2].file_hash,
            "50339c9cd526778eba486c7b79467d3faf0b000345b1454fc3d59353ddefd250",
        )

    def test_hash_directory_sha512_no_exclusion(self):
        """Verify directory hashing with SHA512 when no exclusions are applied."""
        result = hash_paths([self.test_dir], HashAlgorithm.SHA512, [])

        # Verify the structure and sorting of the result entries
        self.assertEqual(len(result.entries), 7)

        # Spot-check the first entry (sorted primarily by hash)
        self.assertEqual(result.entries[2].rel_path, "subdir2/fileE.txt")
        self.assertEqual(
            result.entries[2].file_hash,
            (
                "1eeb3abec5d192c9a540209a1a60c76bac3e5d20f443c1dc9596070baa410e"
                "3737563ab8206da7212bc4c8d851c195dea0b218e95cbbe3c9202a0cc06f971a89"
            ),
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

    @pytest.mark.skip(reason="ssdeep broken dependency - unreleased")
    @unittest.skip("ssdeep broken dependency - unreleased")
    def test_hash_directory_ssdeep(self):
        """Verify directory hashing with the ssdeep algorithm."""
        result = hash_paths([self.test_dir], HashAlgorithm.SSDEEP, [])
        self.assertTrue(len(result.entries) > 0)
        self.assertEqual(len(result.aggregate_hash), 40)
        self.assertEqual(result.entries[2].rel_path, "subdir2/fileE.txt")
        self.assertEqual(
            result.entries[2].file_hash,
            "3:TgmiRqmHR:TgmiR1R",
        )

    def test_hash_directory_tlsh(self):
        """Verify directory hashing with the tlsh algorithm."""
        result = hash_paths([self.test_dir], HashAlgorithm.TLSH, [])
        EXPECTED_HASH_LENGTH = 72
        self.assertTrue(len(result.entries) > 0)
        self.assertTrue(
            all(
                (len(h.file_hash) == EXPECTED_HASH_LENGTH or len(h.file_hash) == 0)
                for h in result.entries
            )
        )
        self.assertEqual(len(result.aggregate_hash), 40)
        self.assertEqual(result.entries[5].rel_path, "subdir2/fileE.txt")
        self.assertEqual(
            result.entries[5].file_hash,
            "",
        )
        self.assertEqual(result.entries[6].rel_path, "subdir2/fileF.txt")
        self.assertEqual(
            result.entries[6].file_hash,
            "T1DBD09524A6514D7D1F175ADC504E44DF554FCDE301C5002517F146D1C510194440ED1D",
        )

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
