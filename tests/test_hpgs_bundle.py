"""Release bundle of the UCSF-PDGM cohort inputs: selection, cleaning, pinning, fetch."""

import json
import zipfile

import pytest
from test_hpgs_cohort import _subject

from glioma_ai import hpgs_bundle as hb
from glioma_ai import hpgs_cohort


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    monkeypatch.setattr(
        hpgs_cohort,
        "published_imaging_reference",
        lambda: {
            "evaluation": {
                "median_dice": {"whole_tumor": 0.9, "tumor_core": 0.94, "enhancing_tumor": 0.86}
            }
        },
    )
    root = (tmp_path / "companion").resolve()
    for subject, shift in (("0001", 0), ("0002", 1), ("0003", 2)):
        _subject(root, subject, shift)
        record = root / f"data/derivatives_cohort50/sub-{subject}/seg_dl"
        (record / f"sub-{subject}_seg_brats3_dl.json").write_text(
            json.dumps({"label_map": str(record / "x.nii.gz"), "cache": "/Users/x/y z"})
        )
    return root


def test_build_selects_cohort_files_and_one_t1c_deterministically(checkout, tmp_path):
    first = hb.build_bundle(checkout, tmp_path / "one")
    second = hb.build_bundle(checkout, tmp_path / "two")
    assert first["sha256"] == second["sha256"]
    assert (first["files"], first["subjects"], first["figure_case"]) == (13, 3, "0002")
    with zipfile.ZipFile(first["archive"]) as zf:
        names = zf.namelist()
        record = json.loads(
            zf.read(
                f"{hb.BUNDLE_NAME}/data/derivatives_cohort50/sub-0001/seg_dl/"
                "sub-0001_seg_brats3_dl.json"
            )
        )
        readme = zf.read(f"{hb.BUNDLE_NAME}/README.md").decode()
    assert [name for name in names if "T1c" in name] == [
        f"{hb.BUNDLE_NAME}/data/ucsf_pdgm_cohort50/sub-0002/sub-0002_T1c_bias.nii.gz"
    ]
    assert record == {
        "cache": "<local path removed> z",
        "label_map": "data/derivatives_cohort50/sub-0001/seg_dl/x.nii.gz",
    }
    assert "CC BY 4.0" in readme and "10.7937/tcia.bdgf-8v37" in readme


def test_extracted_bundle_reproduces_the_cohort_table(checkout, tmp_path, monkeypatch):
    built = hb.build_bundle(checkout, tmp_path / "out")
    reference = {"sha256": built["sha256"], "repository": "x/y", "tag": "t", "asset": "a.zip"}
    result = hb.fetch_bundle(tmp_path / "data", zip_path=built["archive"], reference=reference)
    monkeypatch.setenv("HPGS_REPO", result["checkout"])
    extracted = hpgs_cohort.companion_checkout()
    assert extracted is not None and result["subjects"] == 3
    assert hpgs_cohort.cohort_table(extracted) == hpgs_cohort.cohort_table(checkout)
    again = hb.fetch_bundle(tmp_path / "data", zip_path=built["archive"], reference=reference)
    assert again["downloaded"] is False and again.keys() == result.keys()


def test_unpinned_zip_and_missing_inputs_are_refused(checkout, tmp_path):
    built = hb.build_bundle(checkout, tmp_path / "out")
    reference = {"sha256": "0" * 64, "repository": "x/y", "tag": "t", "asset": "a.zip"}
    with pytest.raises(ValueError, match="pinned SHA-256"):
        hb.fetch_bundle(tmp_path / "data", zip_path=built["archive"], reference=reference)
    (checkout / "data/derivatives_cohort50/sub-0003/seg_dl/sub-0003_seg_brats3_dl.json").unlink()
    with pytest.raises(FileNotFoundError, match="lacks 1 file"):
        hb.build_bundle(checkout, tmp_path / "again")


def test_pinned_reference_names_the_public_release():
    reference = hb.bundle_reference()
    assert reference["repository"] == "arvidl/AI-assisted-glioma-research"
    assert reference["asset"] == f"{hb.BUNDLE_NAME}_{hb.VERSION}.zip"
    assert len(reference["sha256"]) == 64 and reference["files"] == 201
