"""Pytest file for multi-algorithms/ndjson export."""
# pylint: disable=R0801

import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest  # type: ignore

from hashdir.__main__ import main
from tests.base import HashdirTestCase


def test_help(capsys):
    """Test CLI help."""
    testargs = ["prog", "--help"]
    with patch.object(sys, "argv", testargs):
        try:
            main()
        except SystemExit:
            pass
        output = capsys.readouterr().out
        assert (
            "A command line tool to calculate hashes of directory trees"
            " using various hash\nalgorithms."
        ) in output


class TestExport(HashdirTestCase):
    """Test export hashing functionality."""

    def setUp(self):
        """Initialize the test environment with a known file structure."""
        super().setUp()
        self._create_files_with_known_content()

    def test_single_md5(self):
        """Test CLI MD5 output."""
        testargs = ["prog", "-a", "md5", self.test_dir]
        output_buffer = io.StringIO()

        with patch.object(sys, "argv", testargs):
            with redirect_stdout(output_buffer):
                try:
                    main()
                except SystemExit:
                    pass

        output = output_buffer.getvalue()

        self.assertIn("subdir2/fileE.txt 00958efb88e1841b92055be5b421a795", output)

    def test_single_sha256(self):
        """Test CLI SHA256 output."""
        testargs = ["prog", "-a", "sha256", self.test_dir]
        output_buffer = io.StringIO()

        with patch.object(sys, "argv", testargs):
            with redirect_stdout(output_buffer):
                try:
                    main()
                except SystemExit:
                    pass

        output = output_buffer.getvalue()

        self.assertIn(
            (
                "subdir2/fileE.txt "
                "50339c9cd526778eba486c7b79467d3faf0b000345b1454fc3d59353ddefd250"
            ),
            output,
        )

    def test_multi_worker1(self):
        """Test CLI multi-algorithms with one worker."""
        testargs = [
            "prog",
            "-m",
            "md5,sha1,sha512",
            "--workers",
            "1",
            "-o",
            "/tmp/hashes.ndjson",
            self.test_dir,
        ]
        output_buffer = io.StringIO()

        with patch.object(sys, "argv", testargs):
            with redirect_stdout(output_buffer):
                with self.assertLogs(level="INFO") as log:
                    try:
                        main()
                    except SystemExit:
                        pass

        output_buffer.getvalue()
        logs = log.output

        self.assertTrue(any("Scanning: /tmp/test_dir" in msg for msg in logs))
        self.assertTrue(any("Output: /tmp/hashes.ndjson" in msg for msg in logs))
        self.assertTrue(
            any("Completed: 7 files hashed, 0 errors." in msg for msg in logs)
        )
        self.assertFalse(any("ERROR" in msg for msg in logs))
        with open("/tmp/hashes.ndjson", encoding="ascii") as file:
            hashes = file.read()
            self.assertIn(
                (
                    '{"FileName":"fileE.txt","FileSize":"9","CRC32":"8BF74A8B",'
                    '"MD5":"00958EFB88E1841B92055BE5B421A795",'
                    '"SHA-1":"AF3F9FEC8299719239845A77DED518E06A8DBEED",'
                    '"SHA-512":"1EEB3ABEC5D192C9A540209A1A60C76BAC3E5D20F443C1D'
                    "C9596070BAA410E3737563AB8206DA7212BC4C8D851C195DEA0B218E95"
                    'CBBE3C9202A0CC06F971A89"}'
                ),
                hashes,
            )

    @pytest.mark.skip(
        reason=(
            "Separate testing without pyfakefs to avoid threading Lock"
            " - intermittent FileNotFoundError"
        )
    )
    @unittest.skip(
        "Separate testing without pyfakefs to avoid threading Lock"
        " - intermittent FileNotFoundError"
    )
    def test_multi_worker2(self):
        """Test CLI multi-algorithms with two workers."""
        testargs = [
            "prog",
            "-m",
            "md5,sha1,sha512",
            "--workers",
            "2",
            "-o",
            "/tmp/hashes.ndjson",
            self.test_dir,
        ]
        output_buffer = io.StringIO()

        with patch.object(sys, "argv", testargs):
            with redirect_stdout(output_buffer):
                with self.assertLogs(level="INFO") as log:
                    try:
                        main()
                    except SystemExit:
                        pass

        output_buffer.getvalue()
        logs = log.output

        self.assertTrue(any("Scanning: /tmp/test_dir" in msg for msg in logs))
        self.assertTrue(any("Output: /tmp/hashes.ndjson" in msg for msg in logs))
        self.assertTrue(
            any("Completed: 7 files hashed, 0 errors." in msg for msg in logs)
        )
        self.assertFalse(any("ERROR" in msg for msg in logs))
        with open("/tmp/hashes.ndjson", encoding="ascii") as file:
            hashes = file.read()
            self.assertIn(
                (
                    '{"FileName":"fileE.txt","FileSize":"9","CRC32":"8BF74A8B",'
                    '"MD5":"00958EFB88E1841B92055BE5B421A795",'
                    '"SHA-1":"AF3F9FEC8299719239845A77DED518E06A8DBEED",'
                    '"SHA-512":"1EEB3ABEC5D192C9A540209A1A60C76BAC3E5D20F443C1D'
                    "C9596070BAA410E3737563AB8206DA7212BC4C8D851C195DEA0B218E95"
                    'CBBE3C9202A0CC06F971A89"}'
                ),
                hashes,
            )
