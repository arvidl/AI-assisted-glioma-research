"""Release bundle of prepared Patient-048 inputs: selection, path cleaning, pinning, fetch."""

import json
import zipfile

import nibabel as nib
import numpy as np
import pytest
from test_lumiere_dynamics import prepared_fixture

from glioma_ai import lumiere_bundle as lb
from glioma_ai.lumiere_dynamics import prepare_slice_case


def prepared_with_records(tmp_path):
    root = prepared_fixture(tmp_path / "prepared").resolve()
    for folder in (root / "derivatives").glob("tp-*"):
        (folder / "registration_qc.json").write_text(
            json.dumps({"outputs": {"CT1": str(folder / "x.nii.gz")}, "tool": "/opt/ants/bin"})
        )
    parcellation = root / "derivatives/tp-week-045/parcellation"
    parcellation.mkdir()
    nib.save(
        nib.Nifti1Image(np.zeros((9, 11, 6), dtype=np.int32), np.eye(4)),
        parcellation / "tp-week-045_wmparc_native.nii.gz",
    )
    (parcellation / "tp-week-045_wmparc_lut.json").write_text('{"0": "Unknown"}')
    (parcellation / "tp-week-045_wmparc.json").write_text(
        json.dumps({"input_nifti": str(root / "derivatives/a.nii.gz"), "home": "/Users/x/y z"})
    )
    return root


def test_build_is_deterministic_and_cleans_local_paths(tmp_path):
    root = prepared_with_records(tmp_path)
    first = lb.build_bundle(root, tmp_path / "one")
    second = lb.build_bundle(root, tmp_path / "two")
    assert first["sha256"] == second["sha256"] and first["files"] == 27
    with zipfile.ZipFile(first["archive"]) as zf:
        names = zf.namelist()
        assert names[:2] == [
            "lumiere_p048_prepared/README.md",
            "lumiere_p048_prepared/MANIFEST.json",
        ]
        record = json.loads(
            zf.read(
                "lumiere_p048_prepared/derivatives/tp-week-045/parcellation/tp-week-045_wmparc.json"
            )
        )
        manifest = json.loads(zf.read("lumiere_p048_prepared/MANIFEST.json"))
        assert "non-commercial" in zf.read("lumiere_p048_prepared/README.md").decode()
    assert record == {"home": f"{lb.REMOVED} z", "input_nifti": "derivatives/a.nii.gz"}
    rewritten = [f for f in manifest["files"] if "original_sha256" in f]
    assert rewritten and all(f["path"].endswith(".json") for f in rewritten)


def test_missing_inputs_are_refused(tmp_path):
    root = prepared_with_records(tmp_path)
    (root / "derivatives/tp-week-045/parcellation/tp-week-045_wmparc_lut.json").unlink()
    with pytest.raises(FileNotFoundError, match="lacks 1 file"):
        lb.build_bundle(root, tmp_path / "out")


def test_fetch_from_a_local_zip_verifies_extracts_and_loads(tmp_path):
    root = prepared_with_records(tmp_path)
    built = lb.build_bundle(root, tmp_path / "out")
    reference = {"sha256": built["sha256"], "repository": "x/y", "tag": "t", "asset": "a.zip"}
    result = lb.fetch_bundle(tmp_path / "data", zip_path=built["archive"], reference=reference)
    case = prepare_slice_case(tmp_path / "data" / lb.BUNDLE_NAME)
    assert result["files"] == 27 and case.metadata["slice_index"] == 2
    again = lb.fetch_bundle(tmp_path / "data", zip_path=built["archive"], reference=reference)
    assert again["downloaded"] is False and again.keys() == result.keys()
    target = tmp_path / "data" / lb.BUNDLE_NAME / "derivatives/tp-week-045/registration_qc.json"
    target.write_text("{}")
    with pytest.raises(ValueError, match="changed bundle file"):
        lb.fetch_bundle(tmp_path / "data", zip_path=built["archive"], reference=reference)


def test_fetch_refuses_an_unpinned_zip(tmp_path):
    root = prepared_with_records(tmp_path)
    built = lb.build_bundle(root, tmp_path / "out")
    reference = {"sha256": "0" * 64, "repository": "x/y", "tag": "t", "asset": "a.zip"}
    with pytest.raises(ValueError, match="pinned SHA-256"):
        lb.fetch_bundle(tmp_path / "data", zip_path=built["archive"], reference=reference)
    assert not (tmp_path / "data" / lb.BUNDLE_NAME).exists()


def test_pinned_reference_names_the_public_release():
    reference = lb.bundle_reference()
    assert reference["repository"] == "arvidl/AI-assisted-glioma-research"
    assert reference["asset"] == f"{lb.BUNDLE_NAME}_{lb.VERSION}.zip"
    assert len(reference["sha256"]) == 64 and reference["files"] == 27
