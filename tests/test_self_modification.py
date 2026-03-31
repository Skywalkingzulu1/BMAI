import subprocess
import sys
import hashlib
from pathlib import Path
import tempfile


def _file_hash(path: Path) -> str:
    """Return SHA256 hash of a file's contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_rebuild_self_modification_and_determinism():
    # Path to the rebuild script in the project root
    project_root = Path(__file__).resolve().parents[1]
    rebuild_script = project_root / "rebuild.py"
    original_hash = _file_hash(rebuild_script)

    # Create a temporary directory with a sample python file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sample_py = tmp_path / "sample.py"
        sample_py.write_text("def hello():\n    return 'world'\n")

        # First rebuild run
        subprocess.run([sys.executable, str(rebuild_script), str(tmp_path)], check=True)
        # Locate the generated .pyc file
        pyc_file1 = next(tmp_path.rglob("sample*.pyc"))
        hash1 = _file_hash(pyc_file1)

        # Second rebuild run (clean and recompile)
        subprocess.run([sys.executable, str(rebuild_script), str(tmp_path)], check=True)
        pyc_file2 = next(tmp_path.rglob("sample*.pyc"))
        hash2 = _file_hash(pyc_file2)

        # Ensure deterministic bytecode across runs
        assert hash1 == hash2, "Bytecode differs between rebuild runs"

    # Verify that the rebuild script itself was not modified during execution
    after_hash = _file_hash(rebuild_script)
    assert original_hash == after_hash, "rebuild.py was modified during execution"
