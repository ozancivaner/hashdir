import os
import unicodedata
from pathlib import Path, PureWindowsPath
from unittest.mock import patch

from hashdir.core import (
    HashedFileEntry,
    generate_summary,
    get_files_to_hash,
    is_excluded,
    prepare_paths,
)
from tests.base import HashdirTestCase


class TestPathHandling(HashdirTestCase):
    """Test path normalization, exclusion, and summary generation."""

    def test_is_excluded(self):
        """Verify that exclusion patterns correctly match file and directory paths."""
        self.assertTrue(is_excluded("file.txt", ["*.txt"]))
        self.assertTrue(is_excluded("subdir/file.txt", ["*.txt"]))
        self.assertFalse(is_excluded("subdir/file.log", ["*.txt"]))
        self.assertTrue(is_excluded("subdir/file.txt", ["subdir/*.txt"]))
        self.assertTrue(is_excluded("subdir/nested/file.txt", ["subdir/nested/*.txt"]))
        self.assertTrue(is_excluded(".git/config", [".git/*"]))
        self.assertFalse(is_excluded("file.txt", []))
        self.assertTrue(is_excluded("path/to/file.txt", ["path/to/*.txt"]))
        self.assertFalse(is_excluded("path/to/file.txt", ["path/*.txt"]))

        # Verify directory-level exclusion (ancestor matching)
        self.assertTrue(is_excluded("subdir2/fileD.log", ["subdir2"]))
        self.assertTrue(is_excluded("a/b/c/d.txt", ["a/b"]))

    def test_unicode_normalization_for_filenames(self):
        """Verify filename Unicode normalization.

        Ensures NFC/NFD are consistently normalized to NFKD internally.
        """
        unicode_dir = os.path.join(self.test_dir, "unicode_names")
        self.fs.create_dir(unicode_dir)

        # Includes NFC, NFD, and ASCII names to verify NFKD normalization consistency.
        test_cases = [
            (
                unicodedata.normalize("NFC", "café_nfc.txt"),
                "content for NFC named file",
            ),
            (
                unicodedata.normalize("NFD", "café_nfd.txt"),
                "content for NFD named file",
            ),
            (
                unicodedata.normalize("NFC", "regular_ascii.txt"),
                "content for ASCII file",
            ),  # ASCII is NFC
        ]

        for name, content in test_cases:
            self.fs.create_file(os.path.join(unicode_dir, name), contents=content)

        files = get_files_to_hash([unicode_dir], [])

        self.assertEqual(len(files), len(test_cases))

        for f in files:
            # Verify that the relative path is normalized to NFKD regardless
            # of how it was created in the filesystem.
            raw_name = os.path.basename(f.full_path)
            self.assertEqual(f.rel_path, unicodedata.normalize("NFKD", raw_name))

    def test_generate_summary_cross_platform_consistency(self):
        """Ensure backslashes are converted to forward slashes in the summary.

        Maintains consistent aggregate hashes across OSs. This test uses a
        Windows-style path to verify that generate_summary
        standardizes it to POSIX format even when running on non-Windows systems.
        """
        file_hashes = [
            HashedFileEntry(
                root="/tmp",
                rel_path="subdir\\file.txt",
                full_path="/tmp/subdir/file.txt",
                file_hash="abc",
            )
        ]

        with patch("hashdir.core.PurePath", PureWindowsPath):
            summary = generate_summary(file_hashes)
            self.assertEqual(summary, "subdir/file.txt abc\n")

    def test_prepare_paths_exceptions(self):
        """Verify prepare_paths ValueErrors raised for invalid inputs."""
        prepare_paths_dir = os.path.join(self.test_dir, "prepare_paths")
        self.fs.create_dir(prepare_paths_dir)

        symlink_path = os.path.join(prepare_paths_dir, "link_to_fileA.txt")

        self.fs.create_file(
            os.path.join(prepare_paths_dir, "fileA.txt"), contents="content A"
        )

        self.fs.create_symlink(
            symlink_path,
            os.path.join(prepare_paths_dir, "fileA.txt"),
        )

        # Test that non-existent paths raise a ValueError
        with self.assertRaisesRegex(ValueError, "is not a valid directory or file"):
            prepare_paths(["/tmp/non_existent_path_for_test"])

        # Test that symlinks passed as direct arguments raise a ValueError
        with self.assertRaisesRegex(
            ValueError, "is a symlink. Symlinks are not supported as direct arguments"
        ):
            prepare_paths([symlink_path])

    def test_prepare_paths_pruning(self):
        """Verify that prepare_paths correctly prunes redundant overlapping paths."""
        child_dir = os.path.join(self.test_dir, "subdir1")
        child_file = os.path.join(self.test_dir, "fileA.txt")
        self.fs.create_dir(child_dir)
        self.fs.create_file(child_file, contents="test")

        # prepare_paths returns absolute paths as strings.
        # We resolve self.test_dir to be sure it matches the return type.
        root_abs = str(Path(self.test_dir).resolve())

        # Scenario 1: Identical paths
        self.assertEqual(prepare_paths([self.test_dir, self.test_dir]), [root_abs])

        # Scenario 2: Parent and nested directory
        self.assertEqual(prepare_paths([self.test_dir, child_dir]), [root_abs])

        # Scenario 3: Directory and a file inside it
        self.assertEqual(prepare_paths([self.test_dir, child_file]), [root_abs])
