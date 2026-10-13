"""Checks target scientific mistakes: units, geometry, labels, and invalid fits."""

import nibabel as nib
import numpy as np
import pytest

from glioma_ai.growth import (
    exponential_volumes,
    radius_scale_for_exponential_volume,
    slope_shift,
)
from glioma_ai.imaging import load_label_map, summarize_labels
from glioma_ai.metrics import dice_score, fit_log_linear, volume_ml


def save_labels(path, values, affine=None, unit="mm"):
    affine = np.eye(4) if affine is None else affine
    image = nib.Nifti1Image(np.asarray(values, dtype=np.float32), affine)
    image.header.set_xyzt_units(unit)
    nib.save(image, path)
    return path


def test_anisotropic_voxel_units_and_shear():
    affine = np.array([[2, 1, 0, 0], [0, 3, 0, 0], [0, 0, -4, 0], [0, 0, 0, 1]])
    # Two voxels * 24 mm^3 per voxel = 0.048 mL, even under shear/reflection.
    assert volume_ml(np.ones((1, 1, 2)), affine) == pytest.approx(0.048)


def test_dice_empty_disjoint_and_invalid_masks():
    empty = np.zeros((2, 2, 2))
    assert dice_score(empty, empty) == 1
    assert dice_score(empty, np.ones_like(empty)) == 0
    left, right = empty.copy(), empty.copy()
    left[0] = 1
    right[1] = 1
    assert dice_score(left, right) == 0
    with pytest.raises(ValueError, match="binary"):
        dice_score(empty + 0.5, empty)
    with pytest.raises(ValueError, match="same shape"):
        dice_score(empty, np.zeros((1, 2, 2)))


def test_log_linear_recovers_known_rate_and_handles_no_growth():
    days = np.array([0, 10, 20, 40])
    fit = fit_log_linear(days, 2 * np.exp(0.02 * days))
    assert fit["rate_per_day"] == pytest.approx(0.02)
    assert fit["doubling_time_days"] == pytest.approx(np.log(2) / 0.02)
    assert fit_log_linear(days, np.ones(4))["doubling_time_days"] is None
    assert fit_log_linear(days, np.exp(-0.02 * days))["doubling_time_days"] is None


def test_exponential_volume_and_radius_scale_match_the_prescribed_rate():
    days = np.array([0.0, 30.0, 120.0])
    rate = 0.005
    volumes = exponential_volumes(8.0, rate, days)
    assert volumes[0] == pytest.approx(8.0)
    assert volumes[-1] == pytest.approx(8.0 * np.exp(rate * 120))
    assert fit_log_linear(days, volumes)["rate_per_day"] == pytest.approx(rate)
    scales = np.array([radius_scale_for_exponential_volume(rate, day) for day in days])
    assert scales[0] == pytest.approx(1.0)
    assert scales**3 == pytest.approx(np.exp(rate * days))
    assert slope_shift(0.006, rate) == pytest.approx(0.001)
    with pytest.raises(ValueError, match="positive"):
        exponential_volumes(0, rate, days)


@pytest.mark.parametrize(
    "days,volumes",
    [
        ([0, 0, 1], [1, 2, 3]),
        ([0, 1, 2], [1, 0, 3]),
        ([0, 2, 1], [1, 2, 3]),
        ([0, 1, 2], [1, np.nan, 3]),
    ],
)
def test_invalid_longitudinal_inputs(days, volumes):
    with pytest.raises(ValueError):
        fit_log_linear(days, volumes)


def test_nifti_label_selection_and_unit_conversion(tmp_path):
    data = np.array([[[0, 1, 2, 4]]])
    affine = np.diag([0.002, 0.003, 0.004, 1])  # metres
    path = save_labels(tmp_path / "labels.nii.gz", data, affine, "meter")
    result = summarize_labels(path, [1, 4, 9])
    assert result["selected_volume_ml"] == pytest.approx(0.048)
    assert result["missing_selected_labels"] == [9]
    assert result["unselected_nonzero_labels"] == [2]


def test_comparison_rejects_same_shape_different_physical_space(tmp_path):
    values = np.ones((2, 2, 2))
    first = save_labels(tmp_path / "first.nii.gz", values)
    translated = np.eye(4)
    translated[0, 3] = 10
    second = save_labels(tmp_path / "second.nii.gz", values, translated)
    with pytest.raises(ValueError, match="same shape and affine"):
        summarize_labels(first, [1], second)


def test_nifti_unknown_units_probabilities_and_conflicting_forms(tmp_path):
    path = tmp_path / "invalid.nii.gz"
    save_labels(path, np.zeros((2, 2, 2)), unit="unknown")
    with pytest.raises(ValueError, match="Unknown spatial units"):
        load_label_map(path)
    save_labels(path, np.full((2, 2, 2), 0.5))
    with pytest.raises(ValueError, match="integer labels"):
        load_label_map(path)
    image = nib.Nifti1Image(np.zeros((2, 2, 2)), np.eye(4))
    image.header.set_xyzt_units("mm")
    image.set_qform(np.diag([2, 2, 2, 1]), code=1)
    nib.save(image, path)
    with pytest.raises(ValueError, match="qform and sform disagree"):
        load_label_map(path)
