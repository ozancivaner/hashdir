import os

from hashdir.algorithms import HashAlgorithm
from hashdir.core import hash_paths
from tests.base import HashdirTestCase


class TestPinnedRegression(HashdirTestCase):
    """Verify aggregate hash stability using pinned regression baselines."""

    def test_pinned_atomic_md5_baseline(self):
        """PINNED REGRESSION TEST: Verify MD5 hash for a single-file directory.

        This acts as the most basic compatibility contract for summary formatting.
        """
        test_case_dir = os.path.join(self.test_dir, "pinned_atomic_md5")
        self.fs.create_dir(test_case_dir)
        self.fs.create_file(os.path.join(test_case_dir, "café.txt"), contents="hello")

        result = hash_paths([test_case_dir], HashAlgorithm.MD5, [])

        expected_aggregate_hash = "d8c30a9169e5686fe5b3c73edf5919739bcec775"

        self.assertEqual(result.aggregate_hash, expected_aggregate_hash)

    def test_pinned_nested_sha1_baseline(self):
        """PINNED REGRESSION TEST: Verify SHA1 hash for a nested directory structure.

        This tests path normalization, sorting, and aggregate hashing for a
        more complex tree.
        """
        test_case_dir = os.path.join(self.test_dir, "pinned_nested_sha1")
        self.fs.create_dir(test_case_dir)
        self.fs.create_file(os.path.join(test_case_dir, "Δ.txt"), contents="content A")
        self.fs.create_dir(os.path.join(test_case_dir, "v1.0-Δ"))
        self.fs.create_file(
            os.path.join(test_case_dir, "v1.0-Δ", "b.txt"), contents="content B"
        )
        self.fs.create_dir(os.path.join(test_case_dir, "v1.0-Δ", "nested_dir"))
        self.fs.create_file(
            os.path.join(test_case_dir, "v1.0-Δ", "nested_dir", "c.txt"),
            contents="content C",
        )

        result = hash_paths([test_case_dir], HashAlgorithm.SHA1, [])

        expected_aggregate_hash = "efc8f363ff99f3dbf839f8d5d3a52cd41d758846"

        self.assertEqual(result.aggregate_hash, expected_aggregate_hash)

    def test_pinned_directory_exclusion_md5_baseline(self):
        """PINNED REGRESSION TEST: Verify MD5 hash with directory exclusion.

        Confirm consistent pruning of excluded subtrees when a directory is
        explicitly excluded.
        """
        test_case_dir = os.path.join(self.test_dir, "pinned_excluded_md5")
        self.fs.create_dir(test_case_dir)
        self.fs.create_file(
            os.path.join(test_case_dir, "src", "main.py"), contents="print('hello')"
        )
        self.fs.create_dir(os.path.join(test_case_dir, "build"))
        self.fs.create_file(
            os.path.join(test_case_dir, "build", "output.txt"), contents="build log"
        )
        self.fs.create_file(
            os.path.join(test_case_dir, "test", "test.py"), contents="test code"
        )

        result = hash_paths([test_case_dir], HashAlgorithm.MD5, ["build"])

        expected_aggregate_hash = "438e0646434564dfaac74fb82c3bafa90d8b4689"

        self.assertEqual(result.aggregate_hash, expected_aggregate_hash)

    def test_pinned_overlapping_roots_sha1_baseline(self):
        """PINNED REGRESSION TEST: Verify SHA1 hash with overlapping input root paths.

        Ensures prepare_paths and deduplicate_file_entries consistently prune inputs.
        """
        test_case_dir = os.path.join(self.test_dir, "pinned_overlapping_sha1")
        self.fs.create_dir(test_case_dir)
        self.fs.create_file(os.path.join(test_case_dir, "file1.txt"), contents="one")
        nested_dir = os.path.join(test_case_dir, "nested")
        self.fs.create_dir(nested_dir)
        self.fs.create_file(os.path.join(nested_dir, "file2.txt"), contents="two")

        # Pass both the parent directory and the nested directory
        # `prepare_paths` should prune `nested_dir`
        result = hash_paths([test_case_dir, nested_dir], HashAlgorithm.SHA1, [])

        expected_aggregate_hash = "5521501e87d3b448e050c499e69412871ae31e65"

        self.assertEqual(result.aggregate_hash, expected_aggregate_hash)

    def test_pinned_empty_file_md5_baseline(self):
        """PINNED REGRESSION TEST: Verify MD5 hash for an empty file directory.

        Ensure empty files are correctly hashed and included in the summary.
        """
        test_case_dir = os.path.join(self.test_dir, "pinned_empty_file_md5")
        self.fs.create_dir(test_case_dir)
        self.fs.create_file(os.path.join(test_case_dir, "empty.txt"), contents="")

        result = hash_paths([test_case_dir], HashAlgorithm.MD5, [])

        expected_aggregate_hash = "003e3adbfe7f0820bfb7a206e0e440360f85de51"

        self.assertEqual(result.aggregate_hash, expected_aggregate_hash)
