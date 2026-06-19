import os
import unittest

from hashdir.core import (
    get_files_to_hash,
)
from tests.base import HashdirTestCase


class TestDiscovery(HashdirTestCase):
    """Test directory traversal and file discovery logic."""

    def setUp(self):
        """Set up the test environment with specific files and various symlinks."""
        super().setUp()
        self._create_files_with_known_content()

        # Create symlinks (should be ignored by default)
        self.fs.create_symlink(
            os.path.join(self.test_dir, "link_to_fileA.txt"),
            os.path.join(self.test_dir, "fileA.txt"),
        )
        self.fs.create_symlink(
            os.path.join(self.test_dir, "link_to_subdir1"),
            os.path.join(self.test_dir, "subdir1"),
        )
        self.fs.create_symlink(
            os.path.join(self.test_dir, "broken_link"), "/tmp/non_existent_file"
        )
        self.fs.create_symlink(
            os.path.join(self.test_dir, "subdir1", "circular_link"),
            os.path.join(self.test_dir, "subdir1"),
        )
        self.fs.create_file("/tmp/outside_file.txt", contents="outside content")
        self.fs.create_symlink(
            os.path.join(self.test_dir, "link_to_outside"), "/tmp/outside_file.txt"
        )

    def test_get_files_to_hash_with_exclusion(self):
        """Verify that file discovery correctly honors exclusion patterns."""
        # Exclude *.log and subdir2/*
        expected_rel_paths = {
            "empty.txt",
            "fileA.txt",
            "subdir1/fileB.txt",
            "subdir1/nested/fileC.txt",
        }

        files = get_files_to_hash([self.test_dir], ["*.log", "subdir2/*"])
        actual_rel_paths = {f.rel_path for f in files}

        self.assertEqual(actual_rel_paths, expected_rel_paths)
        for f in files:
            self.assertEqual(f.root, self.test_dir)

    def test_get_files_to_hash_symlinks_ignored(self):
        """Ensure that symlinks are ignored during the file discovery process."""
        files = get_files_to_hash([self.test_dir], [])
        rel_paths = [f.rel_path for f in files]

        self.assertNotIn("link_to_fileA.txt", rel_paths)
        self.assertNotIn("link_to_subdir1", rel_paths)
        self.assertNotIn("broken_link", rel_paths)
        self.assertNotIn("subdir1/circular_link", rel_paths)
        self.assertNotIn("link_to_outside", rel_paths)

        self.assertIn("fileA.txt", rel_paths)
        self.assertIn("subdir1/fileB.txt", rel_paths)
        self.assertIn("subdir2/fileD.log", rel_paths)
        self.assertIn("empty.txt", rel_paths)

    def test_get_files_to_hash_permission_error(self):
        """Verify that get_files_to_hash raises PermissionError.

        Triggered when encountering an inaccessible directory during traversal.
        """
        inaccessible_dir = os.path.join(self.test_dir, "inaccessible_dir")
        self.fs.create_dir(inaccessible_dir)
        self.fs.create_file(
            os.path.join(inaccessible_dir, "secret.txt"), contents="shhh"
        )

        # Change permissions to be inaccessible.
        # This will cause os.scandir to raise PermissionError when trying to list its
        # contents.
        self.fs.chmod(inaccessible_dir, 600)

        # Attempt to get files from the parent directory, which contains the
        # inaccessible_dir.
        with self.assertRaises(PermissionError):
            # The error is raised by os.scandir within _scandir_recursive
            list(get_files_to_hash([self.test_dir], []))


if __name__ == "__main__":
    unittest.main()
