"""Small biology-motivated constructions, with prescribed rather than fitted rates.

Neither model predicts a patient's phenotype, neural activity, or treatment
response. The niche cue and slow activity-associated signal are dimensionless
indices. They are not measured cell counts, oxygen tensions, or firing rates.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from glioma_ai.growth import fisher_step_2d


def _unit_plane(values: ArrayLike, name: str) -> NDArray[np.float64]:
    field = np.asarray(values, dtype=float)
    if field.ndim != 2 or min(field.shape) < 3:
        raise ValueError(f"{name} must be a 2D field with at least three points per axis.")
    if not np.isfinite(field).all() or np.any(field < 0) or np.any(field > 1):
        raise ValueError(f"{name} must be finite and between zero and one.")
    return field


def niche_transition(
    other_state: ArrayLike,
    mes_like_state: ArrayLike,
    niche_signal: ArrayLike,
    forward_per_day: float,
    reverse_per_day: float,
    elapsed_days: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Exactly advance a two-state construction with a fixed local niche signal.

    dM/dt = k_forward * s * P - k_reverse * M; dP/dt = -dM/dt.
    P aggregates other tumor states; M is a MES-like program analogue, not a
    measured phenotype. P+M is conserved at each location: no growth, migration,
    death, or immune-cell dynamics are included. Reversibility is an assumed
    teaching choice, not a rate inferred from the cited experiments.
    """
    other = _unit_plane(other_state, "Other state")
    mes = _unit_plane(mes_like_state, "MES-like state")
    signal = _unit_plane(niche_signal, "Niche signal")
    if other.shape != mes.shape or other.shape != signal.shape:
        raise ValueError("State and signal fields must share a grid.")
    total = other + mes
    if np.any(total > 1):
        raise ValueError("The normalized total state abundance cannot exceed one.")
    forward, reverse, elapsed = map(float, (forward_per_day, reverse_per_day, elapsed_days))
    if not np.isfinite([forward, reverse, elapsed]).all() or min(forward, reverse, elapsed) < 0:
        raise ValueError("Rates and elapsed days must be finite and nonnegative.")
    rate = forward * signal + reverse
    equilibrium = np.divide(
        forward * signal * total, rate, out=np.zeros_like(total), where=rate > 0
    )
    next_mes = equilibrium + (mes - equilibrium) * np.exp(-rate * elapsed)
    return total - next_mes, next_mes


@dataclass(frozen=True)
class NeuronGliomaParameters:
    """Phenomenological coefficients; units are in the names, none are fitted."""

    diffusivity_mm2_per_day: float = 0.2
    proliferation_per_day: float = 0.04
    signal_growth_coupling: float = 1.5
    tumor_signal_feedback_per_day: float = 0.12
    signal_relaxation_days: float = 4.0

    def __post_init__(self) -> None:
        values = np.array(
            [
                self.diffusivity_mm2_per_day,
                self.proliferation_per_day,
                self.signal_growth_coupling,
                self.tumor_signal_feedback_per_day,
                self.signal_relaxation_days,
            ],
            dtype=float,
        )
        if not np.isfinite(values).all() or np.any(values[:4] < 0) or values[4] <= 0:
            raise ValueError("Coefficients must be finite and nonnegative; relaxation is positive.")


def neuron_glioma_step_limit(
    parameters: NeuronGliomaParameters, dx_mm: float, dy_mm: float
) -> float:
    """Sufficient explicit-step bound preserving both states in [0,1].

    This includes diffusion AND reaction, plus the signal relaxation/feedback
    bound. It is not merely the diffusion limit. No clipping is performed.
    """
    dx, dy = float(dx_mm), float(dy_mm)
    if not np.isfinite([dx, dy]).all() or min(dx, dy) <= 0:
        raise ValueError("Grid spacings must be finite and positive millimetres.")
    cell_rate = 2 * parameters.diffusivity_mm2_per_day * (
        dx**-2 + dy**-2
    ) + parameters.proliferation_per_day * (1 + parameters.signal_growth_coupling)
    signal_rate = 1 / parameters.signal_relaxation_days + parameters.tumor_signal_feedback_per_day
    return min(1 / cell_rate if cell_rate > 0 else np.inf, 1 / signal_rate)


def neuron_glioma_step(
    density: ArrayLike,
    signal: ArrayLike,
    external_drive: ArrayLike,
    parameters: NeuronGliomaParameters,
    dx_mm: float,
    dy_mm: float,
    dt_days: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Synchronous Euler step for two coarse-grained fields with no-flux density.

    dc/dt = div(D grad c) + rho (1 + kappa*a) c (1-c)
    da/dt = (b-a)/tau + beta*c*(1-a)

    c is normalized density. a is a slow activity-associated growth-signal
    index, NOT voltage or an EEG frequency. b is a prescribed external drive.
    The model has no explicit neurons, synapses, immune cells, or treatment.
    Both updates use the previous fields, not a silently split update.
    """
    cells = _unit_plane(density, "Density")
    activity = _unit_plane(signal, "Signal")
    drive = _unit_plane(external_drive, "External drive")
    if cells.shape != activity.shape or cells.shape != drive.shape:
        raise ValueError("Density, signal, and drive must share a grid.")
    step = float(dt_days)
    if not np.isfinite(step) or step <= 0:
        raise ValueError("The time step must be finite and positive days.")
    if step > neuron_glioma_step_limit(parameters, dx_mm, dy_mm):
        raise ValueError("Time step exceeds the coupled positivity/stability bound.")
    next_density = (
        fisher_step_2d(
            cells,
            parameters.diffusivity_mm2_per_day,
            parameters.proliferation_per_day,
            dx_mm,
            dy_mm,
            step,
        )
        + step
        * parameters.proliferation_per_day
        * parameters.signal_growth_coupling
        * activity
        * cells
        * (1 - cells)
    )
    next_signal = activity + step * (
        (drive - activity) / parameters.signal_relaxation_days
        + parameters.tumor_signal_feedback_per_day * cells * (1 - activity)
    )
    return next_density, next_signal


def well_mixed_neuron_glioma(
    density: float,
    signal: float,
    external_drive: float,
    parameters: NeuronGliomaParameters,
    dt_days: float,
    n_steps: int,
) -> dict[str, NDArray[np.float64]]:
    """Spatially uniform version of the neuron-glioma model, classical RK4.

    dc/dt = rho (1 + kappa*a) c (1-c);  da/dt = (b-a)/tau + beta*c*(1-a).
    Diffusion drops out when the fields are uniform. With kappa = 0 the density
    is the exact logistic curve and with beta = 0 the signal relaxes to b, so
    both limits are available as independent checks.
    """
    values = np.array([density, signal, external_drive], dtype=float)
    if not np.isfinite(values).all() or np.any(values < 0) or np.any(values > 1):
        raise ValueError("Density, signal and drive must be finite and between zero and one.")
    step = float(dt_days)
    if not np.isfinite(step) or step <= 0:
        raise ValueError("The time step must be finite and positive days.")
    if isinstance(n_steps, bool) or not isinstance(n_steps, (int, np.integer)) or n_steps < 1:
        raise ValueError("At least one integer time step is required.")
    rho = parameters.proliferation_per_day
    kappa = parameters.signal_growth_coupling
    beta = parameters.tumor_signal_feedback_per_day
    tau = parameters.signal_relaxation_days
    drive = values[2]

    def rate(state):
        c, a = state
        return np.array(
            [rho * (1 + kappa * a) * c * (1 - c), (drive - a) / tau + beta * c * (1 - a)]
        )

    states = np.empty((n_steps + 1, 2))
    states[0] = values[:2]
    for index in range(n_steps):
        y = states[index]
        k1 = rate(y)
        k2 = rate(y + 0.5 * step * k1)
        k3 = rate(y + 0.5 * step * k2)
        k4 = rate(y + step * k3)
        states[index + 1] = y + step * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return {
        "time_days": np.arange(n_steps + 1) * step,
        "density": states[:, 0],
        "signal": states[:, 1],
    }


def simulate_neuron_glioma(
    density: ArrayLike,
    signal: ArrayLike,
    external_drive: ArrayLike,
    parameters: NeuronGliomaParameters,
    dx_mm: float,
    dy_mm: float,
    dt_days: float,
    n_steps: int,
) -> dict:
    """Return final fields and traces from a stated synthetic construction.

    The integral of normalized density on a 2D grid has units mm^2, not mL,
    cell number, or tumor burden in a patient. Signal means are density-weighted.
    """
    if isinstance(n_steps, bool) or not isinstance(n_steps, (int, np.integer)) or n_steps < 1:
        raise ValueError("At least one integer time step is required.")
    cells = _unit_plane(density, "Density").copy()
    activity = _unit_plane(signal, "Signal").copy()
    integral, weighted_signal = [], []
    for index in range(n_steps + 1):
        total = float(cells.sum())
        integral.append(total * dx_mm * dy_mm)
        weighted_signal.append(float((activity * cells).sum() / total) if total > 0 else 0.0)
        if index < n_steps:
            cells, activity = neuron_glioma_step(
                cells, activity, external_drive, parameters, dx_mm, dy_mm, dt_days
            )
    return {
        "density": cells,
        "signal": activity,
        "time_days": np.arange(n_steps + 1) * dt_days,
        "density_integral_mm2": np.array(integral),
        "density_weighted_signal": np.array(weighted_signal),
    }
