"""Explicit-label NIfTI measurements, with physical geometry checks."""

from pathlib import Path

import nibabel as nib
import numpy as np

from glioma_ai.metrics import dice_score, relative_volume_error, volume_ml, voxel_volume_mm3


def load_label_map(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load a 3D integer label map and return its affine in millimetres.

    Unknown spatial units and conflicting coded qform/sform matrices require
    human resolution. No implicit thresholding, registration, or resampling.
    """
    image = nib.load(path)
    if not isinstance(image, (nib.Nifti1Image, nib.Nifti2Image)):
        raise ValueError("Expected a NIfTI image.")
    if len(image.shape) != 3 or any(size == 0 for size in image.shape):
        raise ValueError("Expected a nonempty 3D label map.")
    units = image.header.get_xyzt_units()[0]
    scales = {"mm": 1.0, "meter": 1000.0, "micron": 0.001}
    if units not in scales:
        raise ValueError("Unknown spatial units; establish the correct units before measuring.")
    qform, qcode = image.get_qform(coded=True)
    sform, scode = image.get_sform(coded=True)
    if not qcode and not scode:
        raise ValueError("No coded spatial transform; establish the physical grid first.")
    if (
        qcode
        and scode
        and not np.allclose(qform[:3] * scales[units], sform[:3] * scales[units], rtol=0, atol=1e-3)
    ):
        raise ValueError("qform and sform disagree; review image geometry before measuring.")
    affine_mm = image.affine.copy()
    affine_mm[:3] *= scales[units]
    voxel_volume_mm3(affine_mm)
    values = np.asarray(image.dataobj)
    if not np.isfinite(values).all() or np.any(values < 0) or np.any(values != np.floor(values)):
        raise ValueError("Segmentation must contain finite nonnegative integer labels.")
    return values, affine_mm


def summarize_labels(path: Path, labels: list[int], reference_path: Path | None = None) -> dict:
    """Measure exactly the requested labels, without assigning tissue meanings."""
    if not labels or any(not isinstance(label, int) or label <= 0 for label in labels):
        raise ValueError("Choose one or more positive integer labels; background is excluded.")
    if len(set(labels)) != len(labels):
        raise ValueError("Labels must be unique.")
    values, affine = load_label_map(path)
    mask = np.isin(values, labels)
    observed = [int(value) for value in np.unique(values)]
    result = {
        "selected_labels": labels,
        "observed_labels": observed,
        "missing_selected_labels": sorted(set(labels) - set(observed)),
        "unselected_nonzero_labels": sorted(set(observed) - set(labels) - {0}),
        "shape": list(values.shape),
        "voxel_volume_mm3": voxel_volume_mm3(affine),
        "affine_mm": affine.tolist(),
        "volume_by_label_ml": {str(label): volume_ml(values == label, affine) for label in labels},
        "selected_volume_ml": volume_ml(mask, affine),
    }
    if reference_path is not None:
        reference, reference_affine = load_label_map(reference_path)
        if reference.shape != values.shape or not np.allclose(
            affine, reference_affine, rtol=0, atol=1e-3
        ):
            raise ValueError("Reference and segmentation must have the same shape and affine.")
        reference_mask = np.isin(reference, labels)
        ref_ml = volume_ml(reference_mask, reference_affine)
        result["comparison"] = {
            "reference_volume_ml": ref_ml,
            "dice": dice_score(mask, reference_mask),
            "relative_volume_error": relative_volume_error(result["selected_volume_ml"], ref_ml),
        }
    return result
