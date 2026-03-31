import os
import sys
import hashlib
import importlib.util
import tempfile
from pathlib import Path

import pytest

# Dynamically import the rebuild module from the project root
rebuild_path = Path(__file__).resolve().parents[1] / "rebuild.py"
spec = importlib.util.spec_from_file_location("rebuild", rebuild_path)
rebuild = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rebuild)


def test_clean_pycache_removes_directories():
    """Ensure clean_pycache deletes all __pycache__ directories recursively."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        cache_dir = root / "module" / "__pycache__"
        cache_dir.mkdir(parents=True)
        dummy_file = cache_dir / "dummy.pyc"
        dummy_file.write_bytes(b"test")
        assert cache_dir.is_dir()
        rebuild.clean_pycache(str(root))
        assert not cache_dir.exists()


def test_compile_source_creates_pyc():
    """compile_source should generate a .pyc file and set PYTHONHASHSEED to 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        py_file = root / "hello.py"
        py_file.write_text("def greet():\n    return 'hi'\n")
        # No __pycache__ before compilation
        assert not any(root.rglob("__pycache__"))
        rebuild.compile_source(str(root))
        # Verify __pycache__ and .pyc existence
        cache_dirs = list(root.rglob("__pycache__"))
        assert cache_dirs, "__pycache__ directory was not created"
        pyc_files = list(cache_dirs[0].glob("hello*.pyc"))
        assert pyc_files, ".pyc file was not generated"
        # Verify environment variable
        assert os.getenv("PYTHONHASHSEED") == "0"


def _hash_pyc(pyc_path: Path) -> str:
    """Return a SHA256 hash of the compiled bytecode file."""
    return hashlib.sha256(pyc_path.read_bytes()).hexdigest()


def test_compile_source_is_deterministic():
    """Running compile_source twice should produce identical .pyc bytecode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        py_file = root / "calc.py"
        py_file.write_text("def add(a, b):\n    return a + b\n")
        # First compilation
        rebuild.compile_source(str(root))
        cache_dir = next(root.rglob("__pycache__"))
        pyc1 = next(cache_dir.glob("calc*.pyc"))
        hash1 = _hash_pyc(pyc1)
        # Clean and re‑compile
        rebuild.clean_pycache(str(root))
        rebuild.compile_source(str(root))
        cache_dir2 = next(root.rglob("__pycache__"))
        pyc2 = next(cache_dir2.glob("calc*.pyc"))
        hash2 = _hash_pyc(pyc2)
        assert hash1 == hash2, "Bytecode differs between deterministic runs"


def test_compile_source_no_py_files():
    """Calling compile_source on a directory without .py files should not fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Empty directory – no .py files
        rebuild.compile_source(str(root))
        # No __pycache__ should be created
        assert not any(root.rglob("__pycache__"))


def test_main_invalid_path(monkeypatch, capsys):
    """The script should exit with an error when the provided path is not a directory."""
    monkeypatch.setattr(sys, "argv", ["rebuild.py", "/nonexistent/path"])
    with pytest.raises(SystemExit) as excinfo:
        rebuild.main()
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert excinfo.value.code == 1
