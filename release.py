#!/usr/bin/env python3
"""
Release script for BMAI project.

Features:
- Runs the test suite to ensure a stable build.
- Builds a Docker image with a version tag.
- Pushes the Docker image to a registry.
- Creates a Git tag for the release and pushes it.

Usage:
    python release.py <version> [--registry REGISTRY] [--dockerfile PATH]

Example:
    python release.py v1.2.3 --registry ghcr.io/youruser/bmai
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(command: list[str], cwd: Path | None = None, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command, raising on failure."""
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=capture_output,
        check=False,
    )
    if result.returncode != 0:
        print(f"Command failed: {' '.join(command)}", file=sys.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout, file=sys.stderr)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result


def run_tests() -> None:
    """Execute the project's test suite."""
    print("Running test suite...")
    run_cmd([sys.executable, "-m", "pytest", "-q"])


def build_docker_image(version: str, registry: str, docker