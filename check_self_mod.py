import sys
from pathlib import Path
from typing import List

from app.self_mod_detection import is_hash_modified, is_marker_modified


def detect_self_modifications(repo_root: Path) -> List[str]:
    """Detect self‑modifications in Python files under *repo_root*.

    This function is pure: it performs no I/O other than reading files via the
    detection utilities and returns a list of human‑readable error messages.
    An empty list indicates no modifications were found.
    """
    py_files = list(repo_root.rglob("*.py"))
    messages: List[str] = []

    for file_path in py_files:
        # Skip hidden directories/files (e.g., .git, .venv)
        if any(part.startswith('.') for part in file_path.parts):
            continue

        if is_hash_modified(file_path):
            messages.append(f"Hash mismatch or missing for {file_path}")

        if is_marker_modified(file_path):
            messages.append(f"Marker '# MODIFIED' found in {file_path}")

    return messages


def main() -> None:
    """Entry point for the CLI tool.

    It delegates the detection work to :func:`detect_self_modifications` and
    handles side‑effects (printing and exiting) based on the results.
    """
    repo_root = Path(__file__).parent
    issues = detect_self_modifications(repo_root)

    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        sys.exit(1)
    else:
        print("No self-modifications detected.")


if __name__ == "__main__":
    main()
