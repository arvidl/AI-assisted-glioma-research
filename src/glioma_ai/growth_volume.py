"""Checked 3D proliferation--invasion on a voxel grid, with an optional domain mask.

Same scheme as ``growth_model.simulate_density_2d``: exact half reaction,
conservative explicit diffusion, exact half reaction. The state is a prescribed
normalized density proxy, not an MRI signal or a cell count. No registration,
resampling, clipping or AI inference occurs.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from glioma_ai.growth_model import logistic_solution


def diffusion_step_limit_3d(diffusivity: ArrayLike, spacing_mm: tuple[float, ...]) -> float:
    """Sufficient bound 1 / (2 max(D) sum(h^-2)) for the explicit update, in days."""
    d = np.asarray(diffusivity, dtype=float)
    h = np.asarray(spacing_mm, dtype=float)
    if d.size == 0 or not np.isfinite(d).all() or np.any(d < 0):
        raise ValueError("Diffusivity must be finite and nonnegative.")
    if h.shape != (3,) or not np.isfinite(h).all() or np.any(h <= 0):
        raise ValueError("Three positive finite spacings in millimetres are required.")
    return np.inf if d.max() == 0 else float(1 / (2 * d.max() * (h**-2).sum()))


def face_conductances(
    diffusivity: ArrayLike, shape: tuple[int, int, int], spacing_mm, domain=None
) -> list[NDArray[np.float64]]:
    """Per-axis face coefficients D_face / h^2; faces leaving ``domain`` are closed."""
    d = np.asarray(diffusivity, dtype=float)
    if d.ndim == 0:
        d = np.full(shape, float(d))
    if d.shape != shape:
        raise ValueError("Diffusivity must be scalar or have the density's shape.")
    faces = []
    for axis, h in enumerate(spacing_mm):
        low = [slice(None)] * 3
        high = [slice(None)] * 3
        low[axis], high[axis] = slice(None, -1), slice(1, None)
        face = 0.5 * (d[tuple(low)] + d[tuple(high)]) / float(h) ** 2
        if domain is not None:
            face = face * (domain[tuple(low)] & domain[tuple(high)])
        faces.append(face)
    return faces


def diffusion_increment(c: NDArray, faces: list[NDArray]) -> NDArray[np.float64]:
    """Discrete div(D grad c) with no flux through the grid boundary."""
    change = np.zeros_like(c)
    for axis, face in enumerate(faces):
        low = [slice(None)] * 3
        high = [slice(None)] * 3
        low[axis], high[axis] = slice(None, -1), slice(1, None)
        flux = face * (c[tuple(high)] - c[tuple(low)])
        change[tuple(low)] += flux
        change[tuple(high)] -= flux
    return change


@dataclass
class VolumeRun:
    """Snapshots (float32) plus a discrete balance audit on a cell-centred 3D grid."""

    days: NDArray[np.float64]
    density: NDArray[np.float32]
    integral_mm3: NDArray[np.float64]
    max_balance_residual_mm3: float
    spacing_mm: tuple[float, float, float]
    n_steps: int
    largest_step_days: float
    step_limit_days: float

    def volumes_cm3(self, threshold: float) -> NDArray[np.float64]:
        """Volume at or above an explicit reading threshold, in cm^3 (1 cm^3 = 1000 mm^3)."""
        level = float(threshold)
        if not np.isfinite(level) or not 0 < level < 1:
            raise ValueError("The reading threshold must be strictly between 0 and 1.")
        voxel = float(np.prod(self.spacing_mm))
        return (self.density >= level).sum(axis=(1, 2, 3)) * voxel / 1000


def simulate_density_3d(
    initial: ArrayLike,
    diffusivity_mm2_per_day: ArrayLike,
    rho_per_day: float,
    days: ArrayLike,
    *,
    spacing_mm: tuple[float, float, float] = (1.0, 1.0, 1.0),
    dt_days: float = 0.2,
    domain: ArrayLike | None = None,
) -> VolumeRun:
    """Forward 3D Fisher--Kolmogorov run; equal steps <= dt_days land on each snapshot.

    No flux crosses the box. A boolean ``domain`` also closes every face between
    a domain voxel and a voxel outside it; the initial density must be zero
    outside it. The stability bound is enforced, never silently relaxed.
    """
    c = np.array(initial, dtype=float, copy=True)
    times = np.asarray(days, dtype=float)
    rho, dt = float(rho_per_day), float(dt_days)
    spacing = tuple(float(h) for h in spacing_mm)
    if c.ndim != 3 or min(c.shape) < 3:
        raise ValueError("Initial density must be a volume with at least three voxels per axis.")
    if not np.isfinite(c).all() or np.any((c < 0) | (c > 1)):
        raise ValueError("Initial normalized density must be finite and in [0, 1].")
    inside = None if domain is None else np.asarray(domain)
    if inside is not None:
        if inside.dtype != bool or inside.shape != c.shape:
            raise ValueError("The domain must be a boolean mask on the initial grid.")
        if np.any(c[~inside] != 0):
            raise ValueError("Initial density must be zero outside the domain.")
    if (
        times.ndim != 1
        or len(times) < 2
        or not np.isfinite(times).all()
        or times[0] != 0
        or np.any(np.diff(times) <= 0)
    ):
        raise ValueError("Snapshot days must start at zero and increase strictly.")
    if not np.isfinite([rho, dt]).all() or rho < 0 or dt <= 0:
        raise ValueError("Reaction rate must be nonnegative and time step positive and finite.")
    limit = diffusion_step_limit_3d(diffusivity_mm2_per_day, spacing)
    if dt > limit:
        raise ValueError(f"Time step {dt:g} exceeds diffusion stability bound {limit:g} days.")
    faces = face_conductances(diffusivity_mm2_per_day, c.shape, spacing, inside)
    voxel = float(np.prod(spacing))
    start_mass = float(c.sum() * voxel)
    snapshots, mass = [c.astype(np.float32)], [start_mass]
    gain, residual, steps, largest = 0.0, 0.0, 0, 0.0
    for start, end in zip(times[:-1], times[1:], strict=True):
        count = int(np.ceil((end - start) / dt))
        step = float((end - start) / count)
        for _ in range(count):
            half = logistic_solution(c, rho, step / 2)
            moved = half + step * diffusion_increment(half, faces)
            if np.any((moved < 0) | (moved > 1)):
                raise ArithmeticError("Diffusion violated the density bounds; no clipping applied.")
            final = logistic_solution(moved, rho, step / 2)
            gain += float(((half - c).sum() + (final - moved).sum()) * voxel)
            c = final
            residual = max(residual, abs(float(c.sum() * voxel) - start_mass - gain))
        steps += count
        largest = max(largest, step)
        snapshots.append(c.astype(np.float32))
        mass.append(float(c.sum() * voxel))
    return VolumeRun(
        times.copy(),
        np.stack(snapshots),
        np.asarray(mass),
        residual,
        spacing,
        steps,
        largest,
        limit,
    )
