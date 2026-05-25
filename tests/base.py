import os

from pyfakefs.fake_filesystem_unittest import TestCase


class HashdirTestCase(TestCase):
    """Base class for hashdir tests providing a fake filesystem."""

    def setUp(self):
        """Initialize the fake filesystem and create a base test directory."""
        self.setUpPyfakefs()
        self.test_dir = "/tmp/test_dir"
        self.fs.create_dir(self.test_dir)

    def _create_files_with_known_content(self):
        """Populate the test directory with a predefined set of files and folders."""
        self.fs.create_dir(os.path.join(self.test_dir, "subdir1"))
        self.fs.create_dir(os.path.join(self.test_dir, "subdir2"))
        self.fs.create_dir(os.path.join(self.test_dir, "subdir1", "nested"))

        self.fs.create_file(
            os.path.join(self.test_dir, "fileA.txt"), contents="content A"
        )
        self.fs.create_file(
            os.path.join(self.test_dir, "subdir1", "fileB.txt"), contents="content B"
        )
        self.fs.create_file(
            os.path.join(self.test_dir, "subdir1", "nested", "fileC.txt"),
            contents="content C",
        )
        self.fs.create_file(
            os.path.join(self.test_dir, "subdir2", "fileD.log"), contents="log content"
        )
        self.fs.create_file(
            os.path.join(self.test_dir, "subdir2", "fileE.txt"), contents="content E"
        )
        self.fs.create_file(os.path.join(self.test_dir, "empty.txt"), contents="")
