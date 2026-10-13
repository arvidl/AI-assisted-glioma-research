"""Checked 2D proliferation--invasion experiments, with physical units.

This module supplements the original forward-Euler teaching example. The state
is a prescribed normalized density proxy, not an MRI signal or a cell count.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from glioma_ai.growth import fisher_step_2d


def logistic_solution(values: ArrayLike, rho_per_day: float, days: float) -> NDArray:
    """Exact local reaction flow; fixed points 0 and 1 remain fixed."""
    c = np.asarray(values, dtype=float)
    rho, time = float(rho_per_day), float(days)
    if not np.isfinite(c).all() or np.any((c < 0) | (c > 1)):
        raise ValueError("Normalized density must be finite and in [0, 1].")
    if not np.isfinite([rho, time]).all() or min(rho, time) < 0:
        raise ValueError("Reaction rate and duration must be finite and nonnegative.")
    decay = np.exp(-rho * time)
    return np.divide(c, c + (1 - c) * decay, out=np.zeros_like(c), where=c > 0)


def diffusion_step_limit(diffusivity: ArrayLike, dx_mm: float, dy_mm: float) -> float:
    """Sufficient convex-weight bound for the no-flux diffusion update, in days."""
    d = np.asarray(diffusivity, dtype=float)
    dx, dy = float(dx_mm), float(dy_mm)
    if d.size == 0 or not np.isfinite(d).all() or np.any(d < 0):
        raise ValueError("Diffusivity must be finite and nonnegative.")
    if not np.isfinite([dx, dy]).all() or min(dx, dy) <= 0:
        raise ValueError("Spacings must be positive finite millimetres.")
    return np.inf if d.max() == 0 else float(1 / (2 * d.max() * (dx**-2 + dy**-2)))


@dataclass
class DensityRun:
    """Snapshots plus a discrete balance audit, on a cell-centred rectangular grid."""

    days: NDArray[np.float64]
    density: NDArray[np.float64]
    integral_mm2: NDArray[np.float64]
    reaction_gain_mm2: NDArray[np.float64]
    max_balance_residual_mm2: float
    dx_mm: float
    dy_mm: float
    n_steps: int
    largest_step_days: float
    step_limit_days: float

    def areas_mm2(self, threshold: float) -> NDArray[np.float64]:
        """Area above an explicit display threshold; not a calibrated MRI boundary."""
        level = float(threshold)
        if not np.isfinite(level) or not 0 < level < 1:
            raise ValueError("The display threshold must be strictly between 0 and 1.")
        return (self.density >= level).sum(axis=(1, 2)) * self.dx_mm * self.dy_mm


def simulate_density_2d(
    initial: ArrayLike,
    diffusivity_mm2_per_day: ArrayLike,
    rho_per_day: float,
    days: ArrayLike,
    *,
    dx_mm: float = 1.0,
    dy_mm: float = 1.0,
    dt_days: float = 0.2,
    domain: ArrayLike | None = None,
) -> DensityRun:
    """Exact half reaction, conservative Euler diffusion, exact half reaction.

    No flux crosses the OUTER RECTANGLE. An optional boolean ``domain`` (for
    example an explicit brain mask) also blocks flux across its boundary; the
    initial density must then be zero outside it. Without it there is no
    anatomical boundary. The
    diffusion bound is enforced, not silently fixed. Within each requested time
    interval equal steps <= dt_days land exactly on the snapshot. Diffusion is
    first order in time; symmetric splitting does not make that step second order.
    No density clipping, image registration, resampling or AI inference occurs.
    """
    c = np.array(initial, dtype=float, copy=True)
    times = np.asarray(days, dtype=float)
    d = np.asarray(diffusivity_mm2_per_day, dtype=float)
    rho, dt = float(rho_per_day), float(dt_days)
    if c.ndim != 2 or min(c.shape) < 3:
        raise ValueError("Initial density must be a plane with at least three cells per axis.")
    if not np.isfinite(c).all() or np.any((c < 0) | (c > 1)):
        raise ValueError("Initial normalized density must be finite and in [0, 1].")
    if d.ndim != 0 and d.shape != c.shape:
        raise ValueError("Diffusivity must be scalar or have the initial plane's shape.")
    inside = None if domain is None else np.asarray(domain)
    if inside is not None:
        if inside.dtype != bool or inside.shape != c.shape:
            raise ValueError("The domain must be a boolean mask on the initial plane.")
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
    limit = diffusion_step_limit(d, dx_mm, dy_mm)
    if dt > limit:
        raise ValueError(f"Time step {dt:g} exceeds diffusion stability bound {limit:g} days.")
    area = dx_mm * dy_mm
    start_mass = float(c.sum() * area)
    snapshots, mass, reaction = [c.copy()], [start_mass], [0.0]
    accumulated_gain, balance_error, steps, largest_step = 0.0, 0.0, 0, 0.0
    for start, end in zip(times[:-1], times[1:], strict=True):
        count = int(np.ceil((end - start) / dt))
        step = float((end - start) / count)
        for _ in range(count):
            half = logistic_solution(c, rho, step / 2)
            transported = fisher_step_2d(half, d, 0.0, dx_mm, dy_mm, step, domain=inside)
            if np.any((transported < 0) | (transported > 1)):
                raise ArithmeticError("Diffusion violated the density bounds; no clipping applied.")
            final = logistic_solution(transported, rho, step / 2)
            accumulated_gain += float(((half - c).sum() + (final - transported).sum()) * area)
            c = final
            balance_error = max(
                balance_error, abs(float(c.sum() * area) - start_mass - accumulated_gain)
            )
        steps += count
        largest_step = max(largest_step, step)
        snapshots.append(c.copy())
        mass.append(float(c.sum() * area))
        reaction.append(accumulated_gain)
    return DensityRun(
        times.copy(),
        np.stack(snapshots),
        np.asarray(mass),
        np.asarray(reaction),
        balance_error,
        dx_mm,
        dy_mm,
        steps,
        largest_step,
        limit,
    )


def solver_controls() -> dict:
    """Independent analytic limits and smooth Neumann-mode spatial refinement.

    Cell centres x=(i+1/2)h on [0,L]; cosine has zero normal derivative at both
    boundaries. dt scales as h^2, so this measures combined discretization error.
    It is a numerical verification, not validation against tumor biology.
    """
    uniform = simulate_density_2d(np.full((9, 11), 0.2), 0.4, 0.07, [0, 10])
    exact = float(logistic_solution(0.2, 0.07, 10))
    rng = np.random.default_rng(2026)
    initial = rng.uniform(0.1, 0.9, (17, 19))
    conserved = simulate_density_2d(initial, rng.uniform(0.1, 0.8, initial.shape), 0, [0, 5])
    convergence = []
    length, d, duration = 20.0, 0.4, 5.0
    for n in (15, 30, 60):
        h = length / n
        x = (np.arange(n) + 0.5) * h
        mode = np.cos(np.pi * x[:, None] / length) * np.cos(np.pi * x[None, :] / length)
        start = 0.4 + 0.2 * mode
        dt = duration / n**2
        run = simulate_density_2d(start, d, 0, [0, duration], dx_mm=h, dy_mm=h, dt_days=dt)
        truth = 0.4 + 0.2 * np.exp(-2 * d * (np.pi / length) ** 2 * duration) * mode
        convergence.append(
            {
                "n": n,
                "spacing_mm": h,
                "dt_days_max": dt,
                "rms_error": float(np.sqrt(np.mean((run.density[-1] - truth) ** 2))),
            }
        )
    return {
        "homogeneous_logistic_max_error": float(np.max(np.abs(uniform.density[-1] - exact))),
        "heterogeneous_diffusion_mass_error_mm2": float(
            abs(conserved.integral_mm2[-1] - conserved.integral_mm2[0])
        ),
        "neumann_cosine_refinement": convergence,
        "verification_scope": "analytic/numerical controls, not clinical validation",
    }
