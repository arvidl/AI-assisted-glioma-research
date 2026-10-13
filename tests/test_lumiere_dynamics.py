"""Geometry, provenance and ROI semantics for the optional fixed-plane adapter."""

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from glioma_ai.lumiere_dynamics import (
    compare_masks,
    export_slice_case,
    load_slice_case,
    prepare_slice_case,
)
from glioma_ai.lumiere_slice import LABEL_SCHEME, VISITS, lumiere_p048_root

REPO_ROOT = Path(__file__).resolve().parents[1]


def prepared_fixture(tmp_path):
    affine = np.eye(4)
    for i, visit in enumerate(VISITS):
        base = tmp_path / "derivatives" / f"tp-{visit['name']}"
        segmentation = base / "seg_dl"
        segmentation.mkdir(parents=True)
        image = nib.Nifti1Image(np.ones((9, 11, 6), dtype=np.float32), affine)
        image.header.set_xyzt_units("mm")
        nib.save(image, base / f"tp-{visit['name']}_CT1_to_ref.nii.gz")
        labels = np.zeros(image.shape, dtype=np.uint8)
        # The starting core chooses z=2; later scans have a larger ROI at z=4.
        labels[3:6, 4:7, 2] = 4
        if i == 5:
            labels[1:8, 1:10, 4] = 4
        else:
            labels[4, 5, 4] = 2
        label_image = nib.Nifti1Image(labels, affine)
        nib.save(label_image, segmentation / f"tp-{visit['name']}_seg_brats3_dl.nii.gz")
        (segmentation / f"tp-{visit['name']}_seg_brats3_dl.json").write_text(
            json.dumps(
                {
                    "backend": "monai_bundle",
                    "bundle_version": "0.4.8",
                    "label_scheme": LABEL_SCHEME,
                    "voxel_spacing_mm": [1, 1, 1],
                    "device": "cpu",
                }
            )
        )
    return tmp_path


def test_starting_visit_selects_the_slice_without_later_label_leakage(tmp_path):
    case = prepare_slice_case(prepared_fixture(tmp_path))
    assert case.metadata["slice_index"] == 2
    assert case.images.shape == (6, 9, 11)
    assert len(case.metadata["source_sha256"]) == 18
    assert case.areas()[4]["core_area_mm2"] == 9
    assert case.roi("week-045", (2,)).sum() == 0
    assert case.metadata["expert_ground_truth"] is False
    assert set(case.metadata["label_header_units"]) == {"unknown"}


def test_slice_export_roundtrip_and_tamper_rejection(tmp_path):
    root = prepared_fixture(tmp_path / "prepared")
    case = prepare_slice_case(root)
    bundle = export_slice_case(case, tmp_path / "slices.npz")
    restored = load_slice_case(bundle)
    np.testing.assert_array_equal(restored.labels, case.labels)
    np.testing.assert_array_equal(restored.images, case.images)
    bundle.write_bytes(bundle.read_bytes() + b"modified")
    with pytest.raises(ValueError, match="SHA-256"):
        load_slice_case(bundle)


def test_geometry_mismatch_is_rejected_without_registration(tmp_path):
    root = prepared_fixture(tmp_path)
    path = root / "derivatives/tp-week-049/tp-week-049_CT1_to_ref.nii.gz"
    affine = np.eye(4)
    affine[0, 3] = 2
    image = nib.Nifti1Image(np.ones((9, 11, 6), dtype=np.float32), affine)
    image.header.set_xyzt_units("mm")
    nib.save(image, path)
    with pytest.raises(ValueError, match="geometry differ"):
        prepare_slice_case(root)


def test_unknown_label_rejected_instead_of_relabeling(tmp_path):
    root = prepared_fixture(tmp_path)
    path = root / "derivatives/tp-week-049/seg_dl/tp-week-049_seg_brats3_dl.nii.gz"
    labels = np.zeros((9, 11, 6), dtype=np.uint8)
    labels[4, 5, 2] = 3
    nib.save(nib.Nifti1Image(labels, np.eye(4)), path)
    with pytest.raises(ValueError, match="Unknown"):
        prepare_slice_case(root)


def test_comparison_counts_are_areas_and_empty_sets_are_defined():
    p, y = np.zeros((4, 5), dtype=bool), np.zeros((4, 5), dtype=bool)
    assert compare_masks(p, y, 2)["dice"] == 1
    p[1, 1:3] = True
    y[1, 2:4] = True
    values = compare_masks(p, y, 2)
    assert values["dice"] == 0.5
    assert values["predicted_area_mm2"] == 4
    assert values["missed_label_area_mm2"] == values["additional_model_area_mm2"] == 2


@pytest.mark.skipif(
    lumiere_p048_root(REPO_ROOT) is None, reason="explicit prepared LUMIERE input absent"
)
def test_explicit_real_case_retains_six_visits_and_physical_geometry():
    case = prepare_slice_case(lumiere_p048_root(REPO_ROOT))
    assert case.metadata["slice_index"] >= 0
    assert case.images.shape[0] == case.labels.shape[0] == 6
    assert len(case.metadata["source_sha256"]) >= 18
    assert case.roi("week-045").any()
    assert case.dx_mm == pytest.approx(1, abs=1e-3)
    assert case.dy_mm == pytest.approx(1, abs=1e-3)
