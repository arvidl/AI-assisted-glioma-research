"""Optional notebook inputs control skipping without silent substitution."""

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_notebooks.py"
spec = importlib.util.spec_from_file_location("check_notebooks", SCRIPT)
assert spec is not None and spec.loader is not None
check_notebooks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_notebooks
spec.loader.exec_module(check_notebooks)


def test_lumiere_notebook_skips_only_when_no_explicit_case_is_configured(tmp_path, monkeypatch):
    monkeypatch.delenv("LUMIERE_P048_ROOT", raising=False)
    monkeypatch.delenv("LUMIERE_P048_SLICE_BUNDLE", raising=False)
    monkeypatch.setattr(check_notebooks, "lumiere_p048_root", lambda: None)
    assert check_notebooks.skip_reason("03_lumiere_prepared_slice.ipynb", tmp_path) is not None


def test_lumiere_notebook_runs_when_an_explicit_slice_bundle_is_configured(tmp_path, monkeypatch):
    bundle = tmp_path / "prepared-slices.npz"
    bundle.write_bytes(b"test bundle placeholder")
    monkeypatch.delenv("LUMIERE_P048_ROOT", raising=False)
    monkeypatch.setenv("LUMIERE_P048_SLICE_BUNDLE", str(bundle))
    monkeypatch.setattr(check_notebooks, "lumiere_p048_root", lambda: None)
    assert check_notebooks.skip_reason("03_lumiere_prepared_slice.ipynb", tmp_path) is None


def test_lumiere_notebook_runs_when_local_case_configuration_exists(tmp_path, monkeypatch):
    prepared = tmp_path / "prepared-lumiere"
    prepared.mkdir()
    local = tmp_path / "local"
    local.mkdir()
    (local / "lumiere-case.json").write_text(json.dumps({"prepared_root": str(prepared)}))
    monkeypatch.delenv("LUMIERE_P048_ROOT", raising=False)
    monkeypatch.delenv("LUMIERE_P048_SLICE_BUNDLE", raising=False)
    monkeypatch.setattr(check_notebooks, "lumiere_p048_root", lambda: None)
    assert check_notebooks.skip_reason("03_lumiere_prepared_slice.ipynb", tmp_path) is None
