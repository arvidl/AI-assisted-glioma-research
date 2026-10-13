"""Interactive explorers for the potassium (07) and field (08) notebooks.

The scenario functions return plain arrays and the draw_* functions take them,
so both are tested without ipywidgets. The explorers import ipywidgets lazily
(notebooks dependency group). All inputs are prescribed teaching values in the
stated units; nothing is fitted to a recording.
"""

import matplotlib.pyplot as plt
import numpy as np

from glioma_ai.neuroglial import (
    field_from_potential,
    integrate_potassium,
    potassium_equilibrium_mV,
    single_pulse_excess_mM,
)
from glioma_ai.notebook_display import show_figure

BASELINE_K_MM = 3.0
INTRACELLULAR_K_MM = 140.0
TEMPERATURE_C = 37.0
FATE_COLOURS = ("#9ecae1", "#31858f", "#8c8c8c")


def _panel(widgets, controls: dict, show):
    """Slider column above the redrawn figure."""
    return widgets.VBox(
        [widgets.VBox(list(controls.values())), widgets.interactive_output(show, controls)]
    )


def pulse_release(
    amplitude_mM_per_s: float, width_s: float, gap_s: float, dt_s: float, duration_s: float
) -> np.ndarray:
    """Two equal rectangular pulses starting at 2 s, separated by gap_s; one entry per interval."""
    starts = np.arange(round(duration_s / dt_s)) * dt_s
    second = 2 + width_s + gap_s
    inside = ((starts >= 2) & (starts < 2 + width_s)) | (
        (starts >= second) & (starts < second + width_s)
    )
    return np.where(inside, float(amplitude_mM_per_s), 0.0)


def clearance_scenario(
    astro_per_s: float,
    other_per_s: float,
    amplitude_mM_per_s: float = 0.6,
    width_s: float = 4.0,
    gap_s: float = 4.0,
    dt_s: float = 0.01,
    duration_s: float = 30.0,
) -> dict:
    """Excess K, ideal E_K shift and the fate of released K for one prescribed scenario.

    Also solves the same total clearance with the astrocytic and other shares
    swapped, which leaves the excess-K trace unchanged.
    """
    release = pulse_release(amplitude_mM_per_s, width_s, gap_s, dt_s, duration_s)
    trace = integrate_potassium(release, dt_s, astro_per_s, other_per_s)
    swapped = integrate_potassium(release, dt_s, other_per_s, astro_per_s)
    baseline = float(potassium_equilibrium_mV(BASELINE_K_MM, INTRACELLULAR_K_MM, TEMPERATURE_C))
    shift = (
        potassium_equilibrium_mV(
            BASELINE_K_MM + trace["excess_mM"], INTRACELLULAR_K_MM, TEMPERATURE_C
        )
        - baseline
    )
    landmarks = single_pulse_excess_mM(amplitude_mM_per_s, astro_per_s + other_per_s, width_s)
    return {
        **trace,
        "release_mM_per_s": release,
        "equilibrium_shift_mV": shift,
        "swapped_excess_mM": swapped["excess_mM"],
        "swapped_astro_cleared_mM": swapped["astro_cleared_mM"],
        "parameters": {
            "astro_per_s": float(astro_per_s),
            "other_per_s": float(other_per_s),
            "amplitude_mM_per_s": float(amplitude_mM_per_s),
            "width_s": float(width_s),
            "gap_s": float(gap_s),
            "dt_s": float(dt_s),
        },
        "first_pulse": landmarks,
    }


def draw_clearance_state(figure, run: dict) -> None:
    """Excess K with the swapped-share trace, E_K shift, and stacked fate of released K."""
    p = run["parameters"]
    time = run["time_s"]
    axes = figure.subplots(1, 3)
    pulses = np.flatnonzero(np.diff(np.r_[0, run["release_mM_per_s"] > 0, 0]))
    spans = list(zip(time[pulses[::2]], time[pulses[1::2]], strict=True))
    for axis in axes:
        for start, end in spans:
            axis.axvspan(start, end, color="#eef2f4", zorder=-1)
        axis.set_xlabel("Elapsed time (s)")
    axes[0].plot(time, run["excess_mM"], color="#cf704b", lw=2, label="Excess K")
    axes[0].plot(
        time,
        run["swapped_excess_mM"],
        color="black",
        ls=":",
        lw=1.5,
        label=f"Shares swapped (λa={p['other_per_s']:g}, λo={p['astro_per_s']:g})",
    )
    plateau = run["first_pulse"]["plateau_mM"]
    if np.isfinite(plateau):
        axes[0].axhline(plateau, color="#cf704b", lw=0.8, ls="--", label="Plateau q/λ")
    axes[0].set_ylabel("Excess extracellular K (mM)")
    axes[0].set_title("Same total clearance, same trace", loc="left")
    axes[0].legend(fontsize=8, loc="upper right")
    axes[1].plot(time, run["equilibrium_shift_mV"], color="#7467a5", lw=2)
    axes[1].set_ylabel("Change in ideal E_K (mV)")
    axes[1].set_title("Ideal K equilibrium, not membrane voltage", loc="left")
    fate = np.vstack([run["excess_mM"], run["astro_cleared_mM"], run["other_cleared_mM"]])
    axes[2].stackplot(
        time,
        fate,
        colors=FATE_COLOURS,
        labels=("Still extracellular", "Cleared by astrocytes (λa)", "Cleared otherwise (λo)"),
    )
    axes[2].plot(time, run["cumulative_release_mM"], color="black", lw=1, label="Released so far")
    axes[2].set_ylabel("mM-equivalent in the reference volume")
    axes[2].set_title("Where the released K went", loc="left")
    axes[2].legend(fontsize=8, loc="upper left")


def clearance_explorer():
    """Sliders for astrocytic and other clearance, release amplitude, pulse width and gap."""
    import ipywidgets as widgets
    from IPython.display import display

    style = {"description_width": "15em"}
    layout = widgets.Layout(width="36em")
    controls = {
        "astro": widgets.FloatSlider(
            0.8, min=0.0, max=2.0, step=0.05, description="Astrocytic clearance λa (1/s)"
        ),
        "other": widgets.FloatSlider(
            0.1, min=0.0, max=2.0, step=0.05, description="Other clearance λo (1/s)"
        ),
        "amplitude": widgets.FloatSlider(
            0.6, min=0.0, max=2.0, step=0.05, description="Release q (mM/s)"
        ),
        "width": widgets.FloatSlider(
            4.0, min=0.5, max=10.0, step=0.5, description="Pulse width (s)"
        ),
        "gap": widgets.FloatSlider(4.0, min=0.0, max=12.0, step=0.5, description="Gap between (s)"),
    }
    for control in controls.values():
        control.style, control.layout, control.continuous_update = style, layout, False

    def show(astro, other, amplitude, width, gap):
        run = clearance_scenario(astro, other, amplitude, width, gap)
        landmarks = run["first_pulse"]
        figure = plt.figure(figsize=(15, 4.3), constrained_layout=True)
        draw_clearance_state(figure, run)
        total = astro + other
        figure.suptitle(
            f"Total clearance λ = {total:.2f}/s, time constant 1/λ = "
            f"{landmarks['time_constant_s']:.2f} s; first-pulse peak "
            f"{landmarks['peak_mM']:.2f} mM (closed form) vs "
            f"{run['excess_mM'].max():.2f} mM overall maximum",
            fontsize=10,
        )
        show_figure(figure)

    display(_panel(widgets, controls, show))


def sampled_field(
    amplitude_uV: float = 100.0,
    wavelength_mm: float = 2.5,
    n_samples: int = 41,
    offset_uV: float = 0.0,
    noise_uV: float = 0.0,
    seed: int = 0,
    span_mm: tuple[float, float] = (-5.0, 5.0),
) -> dict:
    """A prescribed sinusoidal potential sampled at n points, with offset and white noise.

    The field is estimated from the samples with field_from_potential and
    compared with the analytic field at the sample positions (interior points
    only, where the estimate is a central difference). Noise is seeded.
    """
    if isinstance(n_samples, bool) or int(n_samples) < 3:
        raise ValueError("At least three samples are needed for a spatial derivative.")
    if wavelength_mm <= 0 or noise_uV < 0:
        raise ValueError("Wavelength must be positive and noise nonnegative.")
    k = 2 * np.pi / wavelength_mm
    fine = np.linspace(*span_mm, 1001)
    positions = np.linspace(*span_mm, int(n_samples))
    rng = np.random.default_rng(seed)
    clean = amplitude_uV * np.sin(k * positions)
    recorded = clean + offset_uV + noise_uV * rng.standard_normal(positions.size)
    estimate = field_from_potential(recorded, positions)
    analytic = -amplitude_uV * k * np.cos(k * positions) * 1e-3
    interior = slice(1, -1)
    return {
        "fine_mm": fine,
        "fine_potential_uV": amplitude_uV * np.sin(k * fine) + offset_uV,
        "fine_field_V_per_m": -amplitude_uV * k * np.cos(k * fine) * 1e-3,
        "positions_mm": positions,
        "recorded_uV": recorded,
        "estimated_field_V_per_m": estimate,
        "analytic_field_V_per_m": analytic,
        "spacing_mm": float(positions[1] - positions[0]),
        "samples_per_wavelength": float(wavelength_mm / (positions[1] - positions[0])),
        "peak_field_V_per_m": float(amplitude_uV * k * 1e-3),
        "rms_error_V_per_m": float(
            np.sqrt(np.mean((estimate[interior] - analytic[interior]) ** 2))
        ),
        "parameters": {
            "amplitude_uV": float(amplitude_uV),
            "wavelength_mm": float(wavelength_mm),
            "n_samples": int(n_samples),
            "offset_uV": float(offset_uV),
            "noise_uV": float(noise_uV),
            "seed": int(seed),
        },
    }


def derivative_error_curve(
    amplitude_uV: float,
    wavelength_mm: float,
    noise_uV: float,
    sample_counts: np.ndarray,
    seed: int = 0,
    repeats: int = 20,
) -> dict:
    """RMS field error against sample spacing, with the two leading error terms.

    For a central difference on a sinusoid, truncation error has RMS
    A k^3 dx^2 / (6 sqrt 2) and independent sample noise of SD sigma adds
    sigma / (sqrt 2 dx). Both are converted from µV/mm to V/m (factor 1e-3).
    Empirical errors average the squared error over seeded noise repeats.
    """
    k = 2 * np.pi / wavelength_mm
    spacing, empirical = [], []
    for count in np.asarray(sample_counts, dtype=int):
        errors = [
            sampled_field(amplitude_uV, wavelength_mm, count, 0.0, noise_uV, seed + r)[
                "rms_error_V_per_m"
            ]
            ** 2
            for r in range(repeats)
        ]
        spacing.append(10.0 / (count - 1))
        empirical.append(np.sqrt(np.mean(errors)))
    dx = np.array(spacing)
    truncation = amplitude_uV * k**3 * dx**2 / (6 * np.sqrt(2)) * 1e-3
    noise = noise_uV / (np.sqrt(2) * dx) * 1e-3
    return {
        "spacing_mm": dx,
        "empirical_rms_V_per_m": np.array(empirical),
        "truncation_rms_V_per_m": truncation,
        "noise_rms_V_per_m": noise,
        "best_spacing_mm": float(dx[int(np.argmin(empirical))]),
    }


def draw_sampling_state(figure, run: dict) -> None:
    """Potential with its samples, and analytic versus estimated field component."""
    axes = figure.subplots(1, 2)
    axes[0].plot(
        run["fine_mm"], run["fine_potential_uV"], color="#bbbbbb", lw=1, label="Prescribed φ"
    )
    axes[0].plot(
        run["positions_mm"], run["recorded_uV"], "o-", color="#31858f", ms=3, label="Samples"
    )
    axes[0].set(xlabel="Position (mm)", ylabel="Potential (µV)")
    axes[0].set_title(
        f"{run['parameters']['n_samples']} samples, Δx = {run['spacing_mm']:.3g} mm", loc="left"
    )
    axes[0].legend(fontsize=8, loc="upper right")
    axes[1].plot(
        run["fine_mm"], run["fine_field_V_per_m"], color="#bbbbbb", lw=1, label="Analytic E"
    )
    axes[1].plot(
        run["positions_mm"],
        run["estimated_field_V_per_m"],
        "o-",
        color="#cf704b",
        ms=3,
        label="Estimated from samples",
    )
    axes[1].set(xlabel="Position (mm)", ylabel="Field component E_x (V/m)")
    axes[1].set_title(f"RMS error {run['rms_error_V_per_m']:.3g} V/m", loc="left")
    axes[1].legend(fontsize=8, loc="upper right")
    for axis in axes:
        axis.axhline(0, color="#dddddd", lw=0.6)


def draw_error_curve(axis, curve: dict, noise_uV: float) -> None:
    """Log-log RMS error against spacing with the truncation and noise terms."""
    dx = curve["spacing_mm"]
    axis.loglog(dx, curve["empirical_rms_V_per_m"], "o", color="black", label="Measured on samples")
    axis.loglog(dx, curve["truncation_rms_V_per_m"], color="#31858f", label="Truncation ∝ Δx²")
    if noise_uV > 0:
        axis.loglog(dx, curve["noise_rms_V_per_m"], color="#cf704b", label="Noise ∝ σ/Δx")
    axis.axvline(curve["best_spacing_mm"], color="#999999", ls=":", lw=1)
    axis.set(xlabel="Sample spacing Δx (mm)", ylabel="RMS field error (V/m)")
    axis.legend(fontsize=8)


def tumour_border_fields(
    amplitude_brain_uV: float = 100.0,
    amplitude_tumour_uV: float = 20.0,
    wavelength_mm: float = 2.5,
    border_width_mm: float = 0.5,
    field_brain_V_per_m: float = 0.05,
    conductivity_ratio: float = 2.0,
    coarse_spacings_mm: tuple[float, ...] = (0.5, 2.5),
    span_mm: tuple[float, float] = (-5.0, 5.0),
    n_points: int = 1001,
) -> dict:
    """Two prescribed one-dimensional pictures of a tumour border at x = 0 mm.

    Brain is at x < 0 and tumour at x > 0. Activity: a sinusoidal potential
    whose amplitude falls from amplitude_brain_uV to amplitude_tumour_uV over a
    tanh border of width border_width_mm. Conductivity: a steady current density
    normal to the border, so E = J/sigma is piecewise constant and the tumour
    field is field_brain_V_per_m / conductivity_ratio (sigma_tumour/sigma_brain).
    Neither is fitted to tissue; no 3D geometry, oedema shell or source model.
    """
    values = (amplitude_brain_uV, amplitude_tumour_uV, wavelength_mm, border_width_mm)
    if min(values) < 0 or wavelength_mm <= 0 or border_width_mm <= 0:
        raise ValueError("Amplitudes must be nonnegative; wavelength and width positive.")
    if conductivity_ratio <= 0 or any(d <= 0 for d in coarse_spacings_mm):
        raise ValueError("Conductivity ratio and spacings must be positive.")
    x = np.linspace(*span_mm, int(n_points))
    k = 2 * np.pi / wavelength_mm
    drop = amplitude_brain_uV - amplitude_tumour_uV
    u = x / border_width_mm
    amplitude = amplitude_brain_uV - drop * 0.5 * (1 + np.tanh(u))
    slope = -drop / (2 * border_width_mm) / np.cosh(u) ** 2
    activity_potential = amplitude * np.sin(k * x)
    border_term = -slope * np.sin(k * x) * 1e-3
    activity_field = border_term - amplitude * k * np.cos(k * x) * 1e-3

    field_tumour = field_brain_V_per_m / conductivity_ratio
    step_field = np.where(x < 0, field_brain_V_per_m, field_tumour)
    step_potential = -np.where(x < 0, field_brain_V_per_m * x, field_tumour * x) * 1e3

    coarse = {}
    for spacing in coarse_spacings_mm:
        count = int(round((span_mm[1] - span_mm[0]) / spacing)) + 1
        positions = np.linspace(*span_mm, count)
        potential = (
            -np.where(positions < 0, field_brain_V_per_m * positions, field_tumour * positions)
            * 1e3
        )
        coarse[float(spacing)] = {
            "positions_mm": positions,
            "estimated_field_V_per_m": field_from_potential(potential, positions),
        }
    return {
        "positions_mm": x,
        "activity_amplitude_uV": amplitude,
        "activity_potential_uV": activity_potential,
        "activity_field_V_per_m": activity_field,
        "activity_border_term_V_per_m": border_term,
        "activity_numerical_field_V_per_m": field_from_potential(activity_potential, x),
        "step_potential_uV": step_potential,
        "step_field_V_per_m": step_field,
        "step_numerical_field_V_per_m": field_from_potential(step_potential, x),
        "coarse": coarse,
        "parameters": {
            "amplitude_brain_uV": float(amplitude_brain_uV),
            "amplitude_tumour_uV": float(amplitude_tumour_uV),
            "wavelength_mm": float(wavelength_mm),
            "border_width_mm": float(border_width_mm),
            "field_brain_V_per_m": float(field_brain_V_per_m),
            "field_tumour_V_per_m": float(field_tumour),
            "conductivity_ratio": float(conductivity_ratio),
        },
    }


def draw_tumour_border(figure, run: dict) -> None:
    """Activity and conductivity pictures of a border at 0 mm; tumour side shaded."""
    axes = figure.subplots(2, 2, sharex=True)
    x = run["positions_mm"]
    p = run["parameters"]
    axes[0, 0].plot(x, run["activity_potential_uV"], color="#31858f", lw=1.5, label="Potential")
    axes[0, 0].plot(
        x, run["activity_amplitude_uV"], color="#888888", ls="--", lw=1, label="Activity amplitude"
    )
    axes[0, 0].set(ylabel="Potential (µV)")
    axes[0, 0].set_title(
        f"Activity {p['amplitude_brain_uV']:g} → {p['amplitude_tumour_uV']:g} µV across the border",
        loc="left",
        fontsize=10,
    )
    axes[0, 1].plot(x, run["activity_field_V_per_m"], color="#cf704b", lw=1.5, label="Field E_x")
    axes[0, 1].plot(
        x,
        run["activity_border_term_V_per_m"],
        color="black",
        lw=1,
        ls=":",
        label="Border term −A′(x) sin(kx)",
    )
    axes[0, 1].set(ylabel="Field component E_x (V/m)")
    axes[0, 1].set_title("Field follows the local activity", loc="left", fontsize=10)
    axes[1, 0].plot(x, run["step_potential_uV"], color="#31858f", lw=1.5)
    axes[1, 0].set(ylabel="Potential (µV)", xlabel="Position across the border (mm)")
    axes[1, 0].set_title(
        f"Steady current, σ_tumour/σ_brain = {p['conductivity_ratio']:g}", loc="left", fontsize=10
    )
    axes[1, 1].plot(x, run["step_field_V_per_m"], color="#cf704b", lw=1.5, label="Exact J/σ")
    styles = (("o", "#31858f"), ("s", "#555555"))
    for (spacing, est), (marker, colour) in zip(run["coarse"].items(), styles, strict=False):
        axes[1, 1].plot(
            est["positions_mm"],
            est["estimated_field_V_per_m"],
            marker + "-",
            color=colour,
            ms=4,
            lw=0.8,
            label=f"Electrodes every {spacing:g} mm",
        )
    axes[1, 1].set(ylabel="Field component E_x (V/m)", xlabel="Position across the border (mm)")
    axes[1, 1].set_ylim(bottom=0)
    axes[1, 1].set_title("The field jumps; coarse sampling smears it", loc="left", fontsize=10)
    for axis in axes.flat:
        axis.axvspan(0, x[-1], color="#f2e6dc", zorder=0)
        axis.axvline(0, color="#999999", lw=0.8)
        axis.axhline(0, color="#dddddd", lw=0.6)
    axes[0, 0].text(-4.9, -0.9 * p["amplitude_brain_uV"], "brain", fontsize=9, color="#555555")
    axes[0, 0].text(
        0.2, -0.9 * p["amplitude_brain_uV"], "tumour (shaded)", fontsize=9, color="#555555"
    )
    for axis in (axes[0, 0], axes[0, 1]):
        axis.legend(fontsize=8, loc="upper right")
    axes[1, 1].legend(fontsize=8, loc="lower left")


def field_explorer():
    """Sliders for amplitude, wavelength, sample count, offset and noise."""
    import ipywidgets as widgets
    from IPython.display import display

    style = {"description_width": "13em"}
    layout = widgets.Layout(width="34em")
    controls = {
        "amplitude": widgets.FloatSlider(
            100, min=10, max=300, step=10, description="Amplitude A (µV)"
        ),
        "wavelength": widgets.FloatSlider(
            2.5, min=0.5, max=10, step=0.25, description="Wavelength λ (mm)"
        ),
        "n_samples": widgets.IntSlider(41, min=5, max=201, step=2, description="Number of samples"),
        "offset": widgets.FloatSlider(
            0, min=-200, max=200, step=10, description="Common offset (µV)"
        ),
        "noise": widgets.FloatSlider(0, min=0, max=20, step=0.5, description="Noise SD σ (µV)"),
    }
    for control in controls.values():
        control.style, control.layout, control.continuous_update = style, layout, False

    def show(amplitude, wavelength, n_samples, offset, noise):
        run = sampled_field(amplitude, wavelength, n_samples, offset, noise)
        figure = plt.figure(figsize=(13, 4.0), constrained_layout=True)
        draw_sampling_state(figure, run)
        figure.suptitle(
            f"Peak analytic field 2πA/λ = {run['peak_field_V_per_m']:.3g} V/m; "
            f"{run['samples_per_wavelength']:.1f} samples per wavelength "
            "(fewer than 2 cannot represent the wave)",
            fontsize=10,
        )
        show_figure(figure)

    display(_panel(widgets, controls, show))
