"""A stalled kernel ends in a timeout and a recorded retry, never in a silent hang.

A cell that never finishes stands in for the intermittent stall seen in CI and
locally, where the runner waited for a kernel message that never arrived. With
the earlier synchronous kernel manager nbclient's cell timeout could not fire,
so such a cell blocked the run indefinitely.
"""

import importlib.util
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("ipykernel")
pytest.importorskip("nbclient")

import nbformat  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_notebooks.py"
spec = importlib.util.spec_from_file_location("check_notebooks_stall", SCRIPT)
assert spec is not None and spec.loader is not None
check_notebooks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_notebooks
spec.loader.exec_module(check_notebooks)


def write_notebook(path: Path, source: str) -> Path:
    notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(source)])
    nbformat.write(notebook, path)
    return path


@pytest.fixture
def spec_root(tmp_path):
    root = tmp_path / "kernels"
    root.mkdir()
    check_notebooks.write_kernel_spec(root)
    return root


@pytest.fixture
def short_timeouts(monkeypatch):
    monkeypatch.setattr(check_notebooks, "CELL_TIMEOUT", 3)
    monkeypatch.setattr(check_notebooks, "IOPUB_TIMEOUT", 3)
    monkeypatch.setattr(check_notebooks, "STALL_SECONDS", 60)


def test_a_stall_is_retried_once_in_a_fresh_kernel(tmp_path, spec_root, short_timeouts):
    # The first kernel hangs; the second finds the marker and finishes.
    notebook = write_notebook(
        tmp_path / "stall_once.ipynb",
        "import time\nfrom pathlib import Path\n"
        "marker = Path('first-attempt')\n"
        "if not marker.exists():\n    marker.touch()\n    time.sleep(600)\n"
        "print('finished')",
    )
    executed, stalls = check_notebooks.execute(notebook, spec_root, tmp_path)
    assert len(stalls) == 1 and "timed out" in stalls[0]
    assert executed.cells[0].outputs[0]["text"] == "finished\n"


def test_a_repeated_stall_fails_within_the_timeouts(tmp_path, spec_root, short_timeouts):
    notebook = write_notebook(tmp_path / "stall.ipynb", "import time\ntime.sleep(600)")
    start = time.monotonic()
    with pytest.raises(RuntimeError, match="stalled in 2 fresh kernels"):
        check_notebooks.execute(notebook, spec_root, tmp_path)
    assert time.monotonic() - start < 60
