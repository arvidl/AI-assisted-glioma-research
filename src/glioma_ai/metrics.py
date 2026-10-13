"""Geometry and descriptive measurements with explicit assumptions."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def binary_mask(values: ArrayLike) -> NDArray[np.bool_]:
    """Require a finite, nonempty 3D binary mask instead of silently thresholding."""
    array = np.asarray(values)
    if array.ndim != 3 or array.size == 0:
        raise ValueError("Expected a nonempty 3D mask.")
    if not np.isfinite(array).all() or not np.isin(array, (0, 1)).all():
        raise ValueError("Mask values must be finite and binary (0 or 1).")
    return array.astype(bool, copy=False)


def voxel_volume_mm3(affine_mm: ArrayLike) -> float:
    """Voxel volume from a voxel-to-world affine expressed in millimetres.

    The absolute determinant handles rotations, reflections, and shear.
    Multiplying column lengths is only correct for orthogonal voxel axes.
    """
    affine = np.asarray(affine_mm, dtype=float)
    if affine.shape != (4, 4) or not np.isfinite(affine).all():
        raise ValueError("Affine must be a finite 4 by 4 matrix.")
    if not np.allclose(affine[3], [0, 0, 0, 1], rtol=0, atol=1e-8):
        raise ValueError("Expected a homogeneous voxel-to-world affine.")
    volume = float(abs(np.linalg.det(affine[:3, :3])))
    if volume <= 0:
        raise ValueError("Affine must be nonsingular.")
    return volume


def volume_ml(mask: ArrayLike, affine_mm: ArrayLike) -> float:
    """Count selected voxels and convert mm^3 to mL (1 mL = 1000 mm^3)."""
    return float(np.count_nonzero(binary_mask(mask)) * voxel_volume_mm3(affine_mm) / 1000)


def dice_score(prediction: ArrayLike, reference: ArrayLike) -> float:
    """Dice on binary arrays already in the SAME physical grid.

    Two empty masks score 1 by convention. An empty/nonempty pair scores 0.
    Array shape alone does not establish physical alignment; NIfTI callers
    must also compare their affines. This function does not resample.
    """
    prediction, reference = binary_mask(prediction), binary_mask(reference)
    if prediction.shape != reference.shape:
        raise ValueError("Masks must have the same shape and physical grid.")
    denominator = int(prediction.sum()) + int(reference.sum())
    return 1.0 if denominator == 0 else float(2 * (prediction & reference).sum() / denominator)


def surface_points_mm(mask: ArrayLike, spacing_mm: ArrayLike = (1.0, 1.0, 1.0)) -> np.ndarray:
    """Centres (in mm) of mask voxels with at least one face neighbour outside the mask.

    Voxels on the array border count as surface. Axes of length one are ignored, so a
    single slice is treated as a 2D mask with in-plane neighbours only. Spacing must
    describe axis-aligned voxels; sheared or rotated grids need their affine applied first.
    """
    array = binary_mask(mask)
    spacing = np.asarray(spacing_mm, dtype=float)
    if spacing.shape != (3,) or not np.isfinite(spacing).all() or np.any(spacing <= 0):
        raise ValueError("Spacing must be three finite positive millimetre values.")
    padded = np.pad(array, 1)
    interior = padded[1:-1, 1:-1, 1:-1].copy()
    for axis in (axis for axis in range(3) if array.shape[axis] > 1):
        for offset in (-1, 1):
            interior &= np.roll(padded, offset, axis=axis)[1:-1, 1:-1, 1:-1]
    return np.argwhere(array & ~interior) * spacing


def _nearest_distances(source: np.ndarray, target: np.ndarray, chunk: int = 2048) -> np.ndarray:
    distances = np.empty(len(source))
    for start in range(0, len(source), chunk):
        block = source[start : start + chunk, None, :] - target[None, :, :]
        distances[start : start + chunk] = np.sqrt((block**2).sum(axis=2)).min(axis=1)
    return distances


def hausdorff95_mm(
    prediction: ArrayLike, reference: ArrayLike, spacing_mm: ArrayLike = (1.0, 1.0, 1.0)
) -> float:
    """95th-percentile Hausdorff distance between mask surfaces, in mm.

    Convention: surfaces are 6-connected boundary voxels (surface_points_mm); the
    result is the larger of the two directed 95th percentiles of nearest-surface
    distances (numpy linear interpolation), as in MONAI's percentile Hausdorff
    distance. Other implementations differ in surface definition and pooling, so
    values are comparable only under the same convention. Empty masks raise.
    """
    prediction, reference = binary_mask(prediction), binary_mask(reference)
    if prediction.shape != reference.shape:
        raise ValueError("Masks must have the same shape and physical grid.")
    if not prediction.any() or not reference.any():
        raise ValueError("HD95 is undefined when either mask is empty.")
    a, b = surface_points_mm(prediction, spacing_mm), surface_points_mm(reference, spacing_mm)
    return float(
        max(
            np.percentile(_nearest_distances(a, b), 95), np.percentile(_nearest_distances(b, a), 95)
        )
    )


def relative_volume_error(predicted_ml: float, reference_ml: float) -> float | None:
    """Signed relative error; undefined for a zero-volume reference."""
    if not np.isfinite([predicted_ml, reference_ml]).all() or min(predicted_ml, reference_ml) < 0:
        raise ValueError("Volumes must be finite and nonnegative.")
    return None if reference_ml == 0 else float((predicted_ml - reference_ml) / reference_ml)


def fit_log_linear(days: ArrayLike, volumes_ml: ArrayLike) -> dict[str, float | None]:
    """Fit log(V) = intercept + rate * day for a descriptive synthetic example.

    At least three distinct, increasing time points and positive volumes are
    required. This is not a biological or treatment-response model. No
    doubling time is reported for a nonpositive fitted rate.
    """
    times, volumes = np.asarray(days, dtype=float), np.asarray(volumes_ml, dtype=float)
    if times.ndim != 1 or times.shape != volumes.shape or times.size < 3:
        raise ValueError("Provide matching 1D arrays with at least three observations.")
    if not np.isfinite(times).all() or not np.isfinite(volumes).all():
        raise ValueError("Time points and volumes must be finite.")
    if np.any(np.diff(times) <= 0) or np.any(volumes <= 0):
        raise ValueError("Times must be strictly increasing and volumes positive.")
    centered = times - times.mean()
    log_volumes = np.log(volumes)
    rate = float(np.dot(centered, log_volumes - log_volumes.mean()) / np.dot(centered, centered))
    baseline = float(np.exp(log_volumes.mean() - rate * times.mean()))
    return {
        "rate_per_day": rate,
        "volume_at_day_zero_ml": baseline,
        "doubling_time_days": float(np.log(2) / rate) if rate > 0 else None,
    }
