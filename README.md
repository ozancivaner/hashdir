# hashdir

[![Tests](https://github.com/ozancivaner/hashdir/actions/workflows/tests.yml/badge.svg)](https://github.com/ozancivaner/hashdir/actions/workflows/tests.yml)
[![Tests (Windows)](https://github.com/ozancivaner/hashdir/actions/workflows/tests-windows.yml/badge.svg)](https://github.com/ozancivaner/hashdir/actions/workflows/tests-windows.yml)
[![Tests (macOS)](https://github.com/ozancivaner/hashdir/actions/workflows/tests-macos.yml/badge.svg)](https://github.com/ozancivaner/hashdir/actions/workflows/tests-macos.yml)
[![Lint](https://github.com/ozancivaner/hashdir/actions/workflows/lint.yml/badge.svg)](https://github.com/ozancivaner/hashdir/actions/workflows/lint.yml)

A command line tool to calculate hash of directory trees using various hash algorithms.

## Installing

The recommended way to install `hashdir` is via pipx, which keeps the dependencies isolated.

```bash
pipx install hashdir
```

To use the `imohash` algorithm (constant-time hashing for large files), install the optional extra:

```bash
pipx install hashdir[imohash]
```

### Installing From Source (Latest)
1. Clone the repository: `git clone https://github.com/user/hashdir.git && cd hashdir`
2. Install using pipx:
   - **Linux**: `pipx install .`
   - **macOS**: `brew install pipx && pipx install .`
   - **Windows**: `pip install pipx && pipx install .`

### Using Docker

To build from source, run:
```bash
docker build . --tag ozancivaner/hashdir
```
In the repository root directory.

To use, mount a local directory as a volume:
```
docker run -v "/path/to/local/dir:/data" ozancivaner/hashdir:latest /data/
```

---

## Usage

```text
usage: hashdir [-h] [-a {md5,sha1,imohash}] [--exclude EXCLUDE]
               [--log-level {debug,info,error}] [-q] [-v]
               [directory_or_file ...]

A command line tool to calculate hashes of directory trees using various hash
algorithms.

positional arguments:
  directory_or_file     directories or files to hash

options:
  -h, --help            show this help message and exit
  -a, --algorithm {md5,sha1,imohash}
                        the hashing algorithm for files. 'imohash' is optional
                        and provides constant-time hashing for large files,
                        but produces approximate results. See documentation
                        for installation.
  --exclude EXCLUDE     exclude a pattern, like .git/* or *.log
  --log-level {debug,info,error}
                        set the logging level.
  -q, --quiet           only output the final hash value.
  -v, --version         show program's version number and exit
```

### Using hashdir As a Library

You can use `hashdir` as a library by importing the `hash_paths` function. This is useful for verifying data integrity within automated workflows or larger applications.

```python
from hashdir.core import hash_paths
from hashdir.algorithms import HashAlgorithm

# The hash_paths function returns a HashdirResult object
result = hash_paths(
    paths=["./my_data"],          # List of directory or file paths
    algorithm=HashAlgorithm.MD5,  # The algorithm for individual files (MD5, SHA1, or IMOHASH)
    excluded=["*.tmp", ".git/*"]  # Optional list of glob patterns to exclude
)

# Access the aggregate SHA1 hash of the entire path set
print(f"Aggregate Hash: {result.aggregate_hash}")

# Iterate over individual file results
# Entries are sorted primarily by hash and secondarily by path
for entry in result.entries:
    print(f"Path: {entry.rel_path}")
    print(f"Hash: {entry.file_hash}")
```

## Algorithm

Hashdir performs the following steps to ensure a deterministic and stable aggregate hash:
- **Path Discovery & Normalization**: Resolves input paths to absolute paths, prunes redundant entries (e.g., if a directory and a file inside it are both provided), and normalizes all discovered paths and provided parameters to the NFKD Unicode form to ensure consistent handling of filenames across different operating systems and locales.
- **Filtering**: Recursively scans directories using `os.scandir` while skipping symlinks and applying exclusion patterns to both files and directories.
- **Hashing**: Computes the hash for each file using the selected algorithm (`md5` by default).
- **Summary Generation**: Creates a summary string where each line contains the POSIX-style relative path and the file's hash, separated by a space.
- **Sorting**: Entries are sorted primarily by their hash value and secondarily by their relative path. This ensures consistency regardless of filesystem traversal order.
- **Aggregation**: Computes the final aggregate directory hash by applying the **SHA1** algorithm to the entire summary string.

## Assumptions and Limitations

*   **Symlinks**: 
    *   **Direct Arguments**: Passing a symlink as a direct input path is not supported and will raise a `ValueError`.
    *   **Traversal**: `hashdir` ignores symlinks (both files and directories) encountered during recursive scanning to prevent infinite loops and ensure the hash reflects actual content.
*   **Hardlinks**: The tool does not perform inode-based deduplication. If multiple hardlinks to the same file exist within the scanned paths, each will be treated and hashed as a separate file entry.
*   **Filesystems**: It is assumed that the tool is operating on a standard local filesystem (POSIX or Windows). Using the tool on specialized, virtual, or network filesystems (like NFS or SMB) might result in unexpected behavior if those systems handle metadata or traversal in non-standard ways.

---

## Compatibility and Versioning

`hashdir` aims for deterministic and stable aggregate hashes for a given directory structure and content. However, changes in the underlying algorithm or implementation details can lead to different aggregate hashes across versions.

*   **Pinned Regression Tests**: The project maintains a suite of "pinned regression tests" (`tests/test_core.py`) that assert specific aggregate hash values for known directory structures and content. These tests serve as a contract, ensuring that future changes do not inadvertently alter the hash output for these specific scenarios.
*   **Backwards Compatibility**:
    *   **Version 0.25.0 vs. 0.24**: The aggregate hash output generated by `hashdir` version `0.25.0` is **not backwards compatible** with version `0.24`. This change was due to refinements in path normalization and file discovery logic to improve determinism and handle edge cases more robustly.
    *   Users relying on `hashdir` for integrity checks across different versions should be aware of these potential breaking changes. It is recommended to re-baseline expected hashes when upgrading to a new major or minor version.

---

## Contributing

Contributions are welcome! To set up your development environment and ensure code quality, follow these steps:

### Setup

1.  **Virtual Environment**: Create and activate a virtual environment to isolate dependencies.
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```
2.  **Install Dependencies**: Install the package in editable mode along with development tools.
    ```bash
    pip install -e ".[dev]"
    ```

### Linting and Testing

Before submitting a Pull Request, please run the linting tools and tests:

*   **Linting**: Use the `Makefile` to run `ruff`.
    *   Check for issues: `make check`
    *   Automatically apply formatting fixes: `make format`
*   **Testing**: Run the test suite to verify your changes.
    ```bash
    make test
    ```
