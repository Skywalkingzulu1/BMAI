#!/usr/bin/env python3
"""
Rebuild compiled Python files (.pyc) from source in a deterministic way.

This script:
1. Removes all existing __pycache__ directories to ensure a clean state.
2. Sets PYTHONHASHSEED to a fixed value (0) to make hash‑based bytecode
   generation deterministic across runs.
3. Re‑compiles all .py files under the given directory (default: current
   working directory) using ``compileall``.
"""

import argparse
import os
import shutil
import compileall
import sys


def clean_pycache(root: str) -> None:
    """
    Recursively delete all ``__pycache__`` directories under ``root``.
    """
    for dirpath, dirnames, _ in os.walk(root):
        if "__pycache__" in dirnames:
            cache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(cache_path)


def compile_source(root: str) -> None:
    """
    Compile all ``.py`` files under ``root`` deterministically.

    The environment variable ``PYTHONHASHSEED`` is set to ``0`` to ensure
    reproducible bytecode hashes.
    """
    os.environ["PYTHONHASHSEED"] = "0"
    # ``force=True`` recompiles even if timestamps match.
    compileall.compile_dir(root, force=True, quiet=1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild .pyc files deterministically."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory of the project (default: current directory)",
    )
    args = parser.parse_args()
    root = os.path.abspath(args.path)

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    clean_pycache(root)
    compile_source(root)
    print(f"Recompiled Python files under {root}")


if __name__ == "__main__":
    main()