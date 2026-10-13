"""Prescribed growth illustrations: an exponential volume and a synthetic PDE.

The functions state a model used to construct visits. They do not estimate a
biological growth rate, a treatment effect, or a response category.
"""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def exponential_volumes(
    volume0_ml: float, rate_per_day: float, days: ArrayLike
) -> NDArray[np.float64]:
    """Return V(t) = V0 * exp(rate * t) for a prescribed curve.

    V0 is millilitres, t is days, and the rate is per day. The result is the
    continuous formula, not a fit and not a voxel count.
    """
    initial = float(volume0_ml)
    rate = float(rate_per_day)
    times = np.asarray(days, dtype=float)
    if times.ndim != 1 or times.size == 0:
        raise ValueError("Days must be a nonempty 1D array.")
    if not np.isfinite(times).all() or not np.isfinite(rate) or not np.isfinite(initial):
        raise ValueError("Volume, rate, and times must be finite.")
    if initial <= 0:
        raise ValueError("Initial volume must be positive.")
    return initial * np.exp(rate * times)


def radius_scale_for_exponential_volume(rate_per_day: float, day: float) -> float:
    """Scale every ellipsoid radius so continuous volume grows as exp(rate * day).

    Ellipsoid volume is proportional to the product of the three radii. A common
    factor s changes that volume by s**3, so s = exp(rate * day / 3) gives
    volume factor exp(rate * day). Voxelization does not preserve the equality.
    """
    rate, time = float(rate_per_day), float(day)
    if not np.isfinite(rate) or not np.isfinite(time):
        raise ValueError("Rate and day must be finite.")
    return float(np.exp(rate * time / 3))


def _as_profile(values: ArrayLike, name: str) -> NDArray[np.float64]:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size < 3:
        raise ValueError(f"{name} must be a 1D profile with at least three points.")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite.")
    return array


def fisher_step(
    concentration: ArrayLike,
    diffusivity: ArrayLike,
    proliferation_per_time: float,
    dx: float,
    dt: float,
) -> NDArray[np.float64]:
    """Advance one explicit step of a one-dimensional Fisher--Kolmogorov equation.

    The equation is dc/dt = d/dx(D dc/dx) + rho c (1-c), with no flux through
    either endpoint. D and rho are prescribed. The step rejects a time increment
    above the explicit diffusion limit dx^2 / (2 max D).
    """
    cells = _as_profile(concentration, "Concentration")
    diffusion = _as_profile(diffusivity, "Diffusivity")
    if cells.shape != diffusion.shape:
        raise ValueError("Concentration and diffusivity must have the same length.")
    if np.any(diffusion < 0):
        raise ValueError("Diffusivity must be nonnegative.")
    spacing, step = float(dx), float(dt)
    growth = float(proliferation_per_time)
    if not np.isfinite([spacing, step, growth]).all() or spacing <= 0 or step <= 0 or growth < 0:
        raise ValueError("Spacing and time step must be positive and proliferation nonnegative.")
    fastest = float(diffusion.max())
    if fastest > 0 and step > spacing * spacing / (2 * fastest):
        raise ValueError("Time step exceeds the explicit diffusion stability limit.")
    face = 0.5 * (diffusion[:-1] + diffusion[1:])
    flux = face * np.diff(cells) / spacing
    divergence = np.zeros_like(cells)
    divergence[0] = flux[0] / spacing
    divergence[-1] = -flux[-1] / spacing
    divergence[1:-1] = (flux[1:] - flux[:-1]) / spacing
    return cells + step * divergence + step * growth * cells * (1.0 - cells)


def integrate_fisher(
    concentration: ArrayLike,
    diffusivity: ArrayLike,
    proliferation_per_time: float,
    dx: float,
    dt: float,
    n_steps: int,
) -> NDArray[np.float64]:
    """Repeat a stable Fisher--Kolmogorov step. The result is not an MRI estimate."""
    steps = int(n_steps)
    if steps < 1:
        raise ValueError("At least one time step is required.")
    cells = _as_profile(concentration, "Concentration")
    for _ in range(steps):
        cells = fisher_step(cells, diffusivity, proliferation_per_time, dx, dt)
    return cells


def _as_plane(values: ArrayLike, name: str) -> NDArray[np.float64]:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or min(array.shape) < 3:
        raise ValueError(f"{name} must be a 2D field with at least three points on each side.")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite.")
    return array


def _diffusivity_plane(values: ArrayLike, shape: tuple[int, int]) -> NDArray[np.float64]:
    array = np.asarray(values, dtype=float)
    if array.ndim == 0:
        array = np.full(shape, float(array))
    if array.shape != shape or not np.isfinite(array).all() or np.any(array < 0):
        raise ValueError("Diffusivity must be a nonnegative field on the concentration grid.")
    return array


def fisher_step_2d(
    concentration: ArrayLike,
    diffusivity: ArrayLike,
    proliferation_per_time: float,
    dx: float,
    dy: float,
    dt: float,
    *,
    domain: ArrayLike | None = None,
) -> NDArray[np.float64]:
    """Advance one explicit step of a two-dimensional Fisher--Kolmogorov equation.

    The equation is dc/dt = div(D grad c) + rho c (1-c), with no flux through
    the boundary of the plane. A scalar diffusivity is applied at every point.
    An optional boolean ``domain`` also closes every face between a domain cell
    and a cell outside it, so no flux crosses the domain boundary.
    The step rejects a time increment above 1 / (2 max(D) (dx^{-2} + dy^{-2})).
    """
    cells = _as_plane(concentration, "Concentration")
    diffusion = _diffusivity_plane(diffusivity, cells.shape)
    inside = None
    if domain is not None:
        inside = np.asarray(domain)
        if inside.dtype != bool or inside.shape != cells.shape:
            raise ValueError("The domain must be a boolean mask on the concentration grid.")
    spacing_x, spacing_y, step = float(dx), float(dy), float(dt)
    growth = float(proliferation_per_time)
    if (
        not np.isfinite([spacing_x, spacing_y, step, growth]).all()
        or min(spacing_x, spacing_y, step) <= 0
        or growth < 0
    ):
        raise ValueError(
            "Spacings and the time step must be positive and proliferation nonnegative."
        )
    fastest = float(diffusion.max())
    if fastest > 0:
        limit = 1.0 / (2.0 * fastest * (spacing_x**-2 + spacing_y**-2))
        if step > limit:
            raise ValueError("Time step exceeds the explicit diffusion stability limit.")
    divergence = np.zeros_like(cells)
    face_x = 0.5 * (diffusion[:-1, :] + diffusion[1:, :])
    face_y = 0.5 * (diffusion[:, :-1] + diffusion[:, 1:])
    if inside is not None:
        face_x = face_x * (inside[:-1, :] & inside[1:, :])
        face_y = face_y * (inside[:, :-1] & inside[:, 1:])
    flux_x = face_x * np.diff(cells, axis=0) / spacing_x
    divergence[0, :] += flux_x[0, :] / spacing_x
    divergence[-1, :] -= flux_x[-1, :] / spacing_x
    divergence[1:-1, :] += (flux_x[1:, :] - flux_x[:-1, :]) / spacing_x
    flux_y = face_y * np.diff(cells, axis=1) / spacing_y
    divergence[:, 0] += flux_y[:, 0] / spacing_y
    divergence[:, -1] -= flux_y[:, -1] / spacing_y
    divergence[:, 1:-1] += (flux_y[:, 1:] - flux_y[:, :-1]) / spacing_y
    return cells + step * divergence + step * growth * cells * (1.0 - cells)


def integrate_fisher_2d(
    concentration: ArrayLike,
    diffusivity: ArrayLike,
    proliferation_per_time: float,
    dx: float,
    dy: float,
    dt: float,
    n_steps: int,
) -> NDArray[np.float64]:
    """Repeat a stable two-dimensional Fisher--Kolmogorov step.

    The inputs are prescribed. The result is not an estimate of a patient rate
    and not a recurrence region.
    """
    steps = int(n_steps)
    if steps < 1:
        raise ValueError("At least one time step is required.")
    cells = _as_plane(concentration, "Concentration")
    for _ in range(steps):
        cells = fisher_step_2d(cells, diffusivity, proliferation_per_time, dx, dy, dt)
    return cells


def threshold_extents(position: ArrayLike, concentration: ArrayLike, threshold: float) -> dict:
    """Distances from zero to the outermost points at or above a threshold.

    Left and right extents are nonnegative. A side with no such point has extent 0.
    Position is a synthetic coordinate, not a patient-image millimetre axis.
    """
    grid = _as_profile(position, "Position")
    cells = _as_profile(concentration, "Concentration")
    if grid.shape != cells.shape:
        raise ValueError("Position and concentration must have the same length.")
    level = float(threshold)
    if not np.isfinite(level):
        raise ValueError("Threshold must be finite.")
    selected = cells >= level
    left = grid[(grid <= 0) & selected]
    right = grid[(grid >= 0) & selected]
    return {
        "left": float(-left.min()) if left.size else 0.0,
        "right": float(right.max()) if right.size else 0.0,
    }


def spatiotemporal_specification() -> dict:
    """Record the equation this repository solves and the tasks it does not do.

    Formulation names the state, the domain, and the fields that are prescribed.
    The solver is an explicit step. Inverse estimation of those fields from
    images, and prediction of a recurrence region, are not performed.
    """
    return {
        "schema": "spatiotemporal-specification-v1",
        "state": "normalized density on a synthetic line",
        "equation": "dc/dt = d/dx(D dc/dx) + rho c (1-c)",
        "coordinate_unit": "synthetic",
        "boundary": "no flux at both ends",
        "fields_prescribed": ["diffusivity", "proliferation", "initial density"],
        "solver": "explicit finite difference",
        "stability_rule": "dt <= dx^2 / (2 max diffusivity)",
        "inverse_estimation": "not_performed",
        "recurrence_prediction": "not_performed",
        "patient_images": "none",
    }


def synthetic_directed_infiltration() -> dict:
    """Compare a uniform diffusivity with one that is larger on the positive side.

    Both runs use the same focal initial density and the same proliferation.
    The coordinate unit is synthetic. Nothing in the result is estimated from MRI.
    """
    position = np.linspace(-40.0, 40.0, 81)
    spacing = float(position[1] - position[0])
    initial = np.exp(-0.5 * (position / 2.0) ** 2)
    low, high = 0.15, 0.80
    proliferation, step, n_steps = 0.04, 0.2, 250
    isotropic_d = np.full_like(position, low)
    directed_d = np.where(position >= 0.0, high, low)
    isotropic = integrate_fisher(initial, isotropic_d, proliferation, spacing, step, n_steps)
    directed = integrate_fisher(initial, directed_d, proliferation, spacing, step, n_steps)
    visible, infiltrative = 0.5, 0.05
    return {
        "position": position,
        "isotropic": isotropic,
        "directed": directed,
        "visible_threshold": visible,
        "infiltrative_threshold": infiltrative,
        "isotropic_visible": threshold_extents(position, isotropic, visible),
        "isotropic_infiltrative": threshold_extents(position, isotropic, infiltrative),
        "directed_visible": threshold_extents(position, directed, visible),
        "directed_infiltrative": threshold_extents(position, directed, infiltrative),
        "parameters": {
            "dx": spacing,
            "dt": step,
            "n_steps": n_steps,
            "proliferation_per_time": proliferation,
            "diffusivity_low": low,
            "diffusivity_high": high,
            "coordinate_unit": "synthetic",
        },
        "specification": spatiotemporal_specification(),
    }


def slope_shift(fitted_per_day: float, reference_per_day: float) -> float:
    """Return fitted slope minus reference slope, both in per-day units."""
    fitted, reference = float(fitted_per_day), float(reference_per_day)
    if not np.isfinite([fitted, reference]).all():
        raise ValueError("Slopes must be finite.")
    return fitted - reference
