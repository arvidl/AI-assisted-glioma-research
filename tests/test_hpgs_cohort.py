"""Reference-versus-model recomputation keeps grids, labels and companion records explicit."""

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from glioma_ai import hpgs_cohort
from glioma_ai.hpgs_cohort import (
    cohort_table,
    companion_checkout,
    load_pair,
    median_case,
    region_metrics,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
LPS = np.diag([-1.0, -1.0, 1.0, 1.0])


def _save(path: Path, values: np.ndarray, affine: np.ndarray = LPS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(values, affine), path)


def _subject(root: Path, subject: str, shift: int = 0, recorded_dice: dict | None = None) -> None:
    reference = np.zeros((12, 12, 6), dtype=np.uint8)
    reference[3:9, 3:9, 1:5] = 2
    reference[4:8, 4:8, 2:4] = 4
    reference[5:7, 5:7, 2:4] = 1
    prediction = np.roll(reference, shift, axis=0)
    images = root / f"data/ucsf_pdgm_cohort50/sub-{subject}"
    derived = root / f"data/derivatives_cohort50/sub-{subject}"
    _save(images / f"sub-{subject}_tumor_segmentation.nii.gz", reference)
    _save(images / f"sub-{subject}_T1c_bias.nii.gz", reference.astype(np.float32))
    _save(derived / f"seg_dl/sub-{subject}_seg_brats3_dl.nii.gz", prediction)
    metrics = region_metrics(reference, prediction, LPS)
    dice = recorded_dice or {region: metrics[region]["dice"] for region in metrics}
    path = derived / f"metrics/sub-{subject}_metrics_dl_vs_gt.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"metrics": {k: {"dice": v} for k, v in dice.items()}}))


def test_checkout_reads_local_config_only_when_repo_root_is_given(tmp_path, monkeypatch):
    monkeypatch.delenv("HPGS_REPO", raising=False)
    checkout = tmp_path / "companion"
    (checkout / "data/derivatives_cohort50").mkdir(parents=True)
    (checkout / "data/ucsf_pdgm_cohort50").mkdir(parents=True)
    (tmp_path / "local").mkdir()
    (tmp_path / "local/hpgs.json").write_text(json.dumps({"checkout": str(checkout)}))
    assert companion_checkout() is None
    assert companion_checkout(tmp_path) == checkout
    monkeypatch.setenv("HPGS_REPO", str(tmp_path / "missing"))
    assert companion_checkout(tmp_path) is None


def test_region_metrics_use_brats_unions_and_signed_volume_error():
    reference = np.zeros((4, 4, 1), dtype=np.uint8)
    reference[0, :2] = 1
    reference[1, :2] = 4
    reference[2, :2] = 2
    prediction = reference.copy()
    prediction[2, :2] = 0
    values = region_metrics(reference, prediction, np.diag([2.0, 1.0, 1.0, 1.0]))
    assert values["TC"]["dice"] == 1
    assert values["WT"]["reference_ml"] == pytest.approx(0.012)
    assert values["WT"]["volume_error_percent"] == pytest.approx(-100 / 3)
    assert values["ET"]["volume_error_percent"] == 0


def test_geometry_mismatch_unknown_labels_and_orientation_are_rejected(tmp_path):
    _subject(tmp_path, "0001")
    path = tmp_path / "data/derivatives_cohort50/sub-0001/seg_dl/sub-0001_seg_brats3_dl.nii.gz"
    _save(path, np.zeros((12, 12, 6), dtype=np.uint8), np.diag([-2.0, -1.0, 1.0, 1.0]))
    with pytest.raises(ValueError, match="geometry differ"):
        load_pair(tmp_path, "0001")
    labels = np.zeros((12, 12, 6), dtype=np.uint8)
    labels[0, 0, 0] = 3
    _save(path, labels)
    with pytest.raises(ValueError, match="Unknown labels"):
        load_pair(tmp_path, "0001")
    _subject(tmp_path / "ras", "0002")
    image = tmp_path / "ras/data/ucsf_pdgm_cohort50/sub-0002/sub-0002_tumor_segmentation.nii.gz"
    _save(image, np.asarray(nib.load(image).dataobj), np.eye(4))
    model = tmp_path / "ras/data/derivatives_cohort50/sub-0002/seg_dl/sub-0002_seg_brats3_dl.nii.gz"
    _save(model, np.asarray(nib.load(model).dataobj), np.eye(4))
    with pytest.raises(ValueError, match="not stored as"):
        load_pair(tmp_path / "ras", "0002")


def test_cohort_table_checks_companion_dice_and_selects_median_case(tmp_path, monkeypatch):
    monkeypatch.setattr(
        hpgs_cohort,
        "published_imaging_reference",
        lambda: {
            "evaluation": {
                "median_dice": {"whole_tumor": 0.9, "tumor_core": 0.94, "enhancing_tumor": 0.86}
            }
        },
    )
    for subject, shift in (("0001", 0), ("0002", 1), ("0003", 2)):
        _subject(tmp_path, subject, shift)
    table = cohort_table(tmp_path)
    assert table["n_subjects"] == 3
    assert table["max_dice_difference_vs_companion"] == 0
    assert table["medians"]["WT"]["n_model_smaller"] == 0
    assert table["medians_match_published_at_two_decimals"] is False
    assert median_case(table) == "0002"
    _subject(tmp_path, "0004", 0, {"WT": 0.5, "TC": 1.0, "ET": 1.0})
    with pytest.raises(ValueError, match="differs from the companion"):
        cohort_table(tmp_path)


@pytest.mark.skipif(
    companion_checkout(REPO_ROOT) is None, reason="companion UCSF-PDGM cohort is absent"
)
def test_configured_cohort_reproduces_published_median_dice():
    table = cohort_table(companion_checkout(REPO_ROOT))
    assert table["n_subjects"] == 50
    assert table["max_dice_difference_vs_companion"] <= 1e-6
    assert table["medians_match_published_at_two_decimals"]
