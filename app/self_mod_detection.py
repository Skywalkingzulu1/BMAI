"""
Self-modification detection utilities.

These utilities provide simple mechanisms to detect whether a source file
has been modified since a reference point. Two strategies are offered:

1. Marker‑based detection: a special comment ``# MODIFIED`` can be inserted
   into a file. The presence of this marker indicates the file has been
   manually flagged as modified.

2. Hash‑based detection: the SHA‑256 hash of a file's contents can be stored
   in a side‑car ``.hash`` file. Subsequent checks compare the current hash
   against the stored value to determine if the file has changed.
"""

import hashlib
from pathlib import Path
from typing import Optional


def _compute_sha256(content: bytes) -> str:
    """Return the SHA‑256 hex digest of *content*."""
    return hashlib.sha256(content).hexdigest()


def get_file_hash(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of the file at *file_path*.

    Parameters
    ----------
    file_path: Path
        Path to the file whose hash is to be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    return _compute_sha256(file_path.read_bytes())


def write_hash_file(file_path: Path, hash_value: Optional[str] = None) -> Path:
    """
    Write the hash of *file_path* to a side‑car ``.hash`` file.

    If *hash_value* is ``None`` the hash is computed on‑the‑fly.

    Returns
    -------
    Path
        Path to the created ``.hash`` file.
    """
    hash_path = file_path.with_suffix(file_path.suffix + ".hash")
    if hash_value is None:
        hash_value = get_file_hash(file_path)
    hash_path.write_text(hash_value, encoding="utf-8")
    return hash_path


def is_hash_modified(file_path: Path) -> bool:
    """
    Determine whether the file at *file_path* differs from the hash stored in its
    ``.hash`` side‑car file.

    Returns ``True`` if the hash file is missing or the hashes differ,
    otherwise ``False``.
    """
    hash_path = file_path.with_suffix(file_path.suffix + ".hash")
    if not hash_path.is_file():
        return True
    stored_hash = hash_path.read_text(encoding="utf-8").strip()
    current_hash = get_file_hash(file_path)
    return stored_hash != current_hash


def is_marker_modified(file_path: Path, marker: str = "# MODIFIED") -> bool:
    """
    Detect the presence of a *marker* comment in *file_path*.

    Returns ``True`` if the marker line exists (ignoring surrounding whitespace),
    otherwise ``False``.
    """
    try:
        for line in file_path.read_text(encoding="utf-8").splitlines():
            if line.strip() == marker:
                return True
    except FileNotFoundError:
        return False
    return False