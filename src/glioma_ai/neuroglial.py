"""Small, unit-explicit constructions; no fitted physiology or cognition model."""

import numpy as np


def _nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not np.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return value


def integrate_potassium(
    release_mM_per_s: np.ndarray,
    dt_s: float,
    astro_clearance_per_s: float,
    other_clearance_per_s: float,
    initial_excess_mM: float = 0,
) -> dict[str, np.ndarray]:
    """Exact one-compartment excess-K solution for piecewise-constant release.

    dk/dt = q - (lambda_astro + lambda_other) k. Each q entry applies over
    one dt interval. Clearance returns excess extracellular K toward an
    implicit baseline; intracellular storage, rerelease, pumps, spatial
    transport, neurons, glioma cells and cognition are not resolved.
    Cumulative fluxes use the same fixed extracellular reference volume.
    No clipping, thresholding or inferred firing-to-release mapping is used.
    """
    release = np.asarray(release_mM_per_s, dtype=float)
    if release.ndim != 1 or not np.isfinite(release).all() or (release < 0).any():
        raise ValueError("release must be a finite nonnegative one-dimensional array")
    dt = _nonnegative(dt_s, "dt_s")
    if dt == 0:
        raise ValueError("dt_s must be positive")
    astro = _nonnegative(astro_clearance_per_s, "astro clearance")
    other = _nonnegative(other_clearance_per_s, "other clearance")
    initial = _nonnegative(initial_excess_mM, "initial excess")
    rate = astro + other
    if not np.isfinite(rate):
        raise ValueError("combined clearance must be finite")
    size = release.size + 1
    excess = np.empty(size)
    excess[0] = initial
    cleared = np.zeros(size)
    fraction = -np.expm1(-rate * dt) if rate else 0
    for index, q in enumerate(release):
        increment = q * dt if rate == 0 else q * fraction / rate
        excess[index + 1] = excess[index] * (1 - fraction) + increment
        removed = excess[index] + q * dt - excess[index + 1]
        cleared[index + 1] = cleared[index] + removed
    if not np.isfinite(excess).all() or not np.isfinite(cleared).all():
        raise ValueError("chosen inputs overflow the concentration representation")
    cumulative_input = np.concatenate(([0.0], np.cumsum(release) * dt))
    return {
        "time_s": np.arange(size) * dt,
        "excess_mM": excess,
        "cumulative_release_mM": cumulative_input,
        "astro_cleared_mM": cleared * astro / rate if rate else np.zeros(size),
        "other_cleared_mM": cleared * other / rate if rate else np.zeros(size),
    }


def single_pulse_excess_mM(
    release_mM_per_s: float, clearance_per_s: float, duration_s: float
) -> dict[str, float]:
    """Closed-form landmarks of one rectangular release pulse starting from zero excess.

    With constant release q over [0, T] and total clearance lambda, the excess
    rises as (q/lambda)(1 - exp(-lambda t)) and decays as exp(-lambda t) after T.
    Returns the plateau q/lambda the pulse approaches, the time constant
    1/lambda and the peak reached at the end of the pulse (q*T when lambda = 0).
    """
    q = _nonnegative(release_mM_per_s, "release")
    rate = _nonnegative(clearance_per_s, "clearance")
    duration = _nonnegative(duration_s, "duration")
    if rate == 0:
        return {"plateau_mM": np.inf, "time_constant_s": np.inf, "peak_mM": q * duration}
    return {
        "plateau_mM": q / rate,
        "time_constant_s": 1 / rate,
        "peak_mM": q / rate * -np.expm1(-rate * duration),
    }


def nernst_slope_mV_per_mM(extracellular_mM: float, temperature_C: float = 37) -> float:
    """Derivative dE_K/d[K]out = (RT/F)/[K]out of the ideal Nernst relation, in mV per mM."""
    outside, kelvin = float(extracellular_mM), float(temperature_C) + 273.15
    if not np.isfinite([outside, kelvin]).all() or outside <= 0 or kelvin <= 0:
        raise ValueError("concentration and absolute temperature must be finite and positive")
    return 1000 * 8.314462618 * kelvin / 96485.33212 / outside


def potassium_equilibrium_mV(
    extracellular_mM: np.ndarray,
    intracellular_mM: float = 140,
    temperature_C: float = 37,
) -> np.ndarray:
    """Ideal K-selective Nernst equilibrium voltage, not membrane voltage.

    R=8.314462618 J/(mol K), F=96485.33212 C/mol, z=+1. Concentrations
    substitute for activities as an explicit ideal-solution assumption.
    Intracellular K and temperature are held fixed; no other ion is modeled.
    """
    outside = np.asarray(extracellular_mM, dtype=float)
    inside, kelvin = float(intracellular_mM), float(temperature_C) + 273.15
    if (
        not np.isfinite(outside).all()
        or (outside <= 0).any()
        or not np.isfinite(inside)
        or inside <= 0
        or not np.isfinite(kelvin)
        or kelvin <= 0
    ):
        raise ValueError("concentrations and absolute temperature must be finite and positive")
    return 1000 * 8.314462618 * kelvin / 96485.33212 * np.log(outside / inside)


def field_from_potential(potential_uV: np.ndarray, coordinates_mm: np.ndarray) -> np.ndarray:
    """Estimate E=-d(phi)/dx in V/m on an explicit 1D sampling line.

    The last potential axis follows the strictly increasing coordinate axis.
    A time-varying trace at one electrode is insufficient. This estimates
    only one field component; it does not reconstruct a 3D field or identify
    current sources, membrane effects, or intracellular fields.
    """
    potential = np.asarray(potential_uV, dtype=float)
    coordinates = np.asarray(coordinates_mm, dtype=float)
    if (
        coordinates.ndim != 1
        or coordinates.size < 3
        or not np.isfinite(coordinates).all()
        or (np.diff(coordinates) <= 0).any()
    ):
        raise ValueError("coordinates must contain at least three finite increasing positions")
    if (
        potential.ndim < 1
        or potential.shape[-1] != coordinates.size
        or not np.isfinite(potential).all()
    ):
        raise ValueError("finite potential must match the last-axis coordinate grid")
    return -np.gradient(potential * 1e-6, coordinates * 1e-3, axis=-1, edge_order=2)
