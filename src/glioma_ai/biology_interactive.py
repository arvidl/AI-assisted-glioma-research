"""Interactive teaching views for notebooks 05 (niche) and 06 (neuron-glioma feedback).

Every field and rate here is a prescribed construction on a constructed 1 mm grid,
not patient space. Scenario functions are pure and tested; explorers add widgets.
"""

from dataclasses import replace
from functools import lru_cache

import numpy as np

from glioma_ai.biology import (
    NeuronGliomaParameters,
    niche_transition,
    simulate_neuron_glioma,
    well_mixed_neuron_glioma,
)
from glioma_ai.notebook_display import show_figure

GRID_MM = np.arange(61, dtype=float) - 30
EXTENT_MM = (-30.5, 30.5, -30.5, 30.5)
CASE_COLOURS = {"baseline": "#555555", "one_way": "#31858f", "feedback": "#d67645"}
CASE_LABELS = {
    "baseline": "Baseline (κ = β = 0)",
    "one_way": "One-way (β = 0)",
    "feedback": "Feedback",
}


def _panel(widgets, controls, show):
    return widgets.VBox([*controls.values(), widgets.interactive_output(show, controls)])


def _sliders(widgets, specs, width="34em", label_width="13em"):
    style = {"description_width": label_width}
    layout = widgets.Layout(width=width)
    controls = {}
    for name, (value, low, high, step, label) in specs.items():
        cls = widgets.IntSlider if isinstance(value, int) else widgets.FloatSlider
        controls[name] = cls(
            value=value,
            min=low,
            max=high,
            step=step,
            description=label,
            continuous_update=False,
            style=style,
            layout=layout,
        )
    return controls


# --- Notebook 05: state composition at fixed abundance -------------------------------


def niche_landmarks(forward_per_day: float, reverse_per_day: float, cue: float) -> dict:
    """Equilibrium MES-like fraction k_f s/(k_f s + k_r) and time constant 1/(k_f s + k_r)."""
    rate = forward_per_day * cue + reverse_per_day
    if rate == 0:
        return {"equilibrium_fraction": np.nan, "time_constant_days": np.inf}
    return {"equilibrium_fraction": forward_per_day * cue / rate, "time_constant_days": 1 / rate}


def well_mixed_fraction(
    forward_per_day: float, reverse_per_day: float, cue: float, days, initial_fraction: float
) -> np.ndarray:
    """Closed-form MES-like fraction m(t) = m* + (m0 - m*) exp(-(k_f s + k_r) t)."""
    days = np.asarray(days, dtype=float)
    rate = forward_per_day * cue + reverse_per_day
    if rate == 0:
        return np.full_like(days, initial_fraction)
    target = forward_per_day * cue / rate
    return target + (initial_fraction - target) * np.exp(-rate * days)


def well_mixed_scenario(
    forward_per_day: float = 0.08,
    reverse_per_day: float = 0.02,
    cue: float = 1.0,
    initial_fraction: float = 0.1,
    rate_scale: float = 2.0,
    horizon_days: float = 80.0,
) -> dict:
    """The fraction for the given rates and for both rates multiplied by rate_scale."""
    days = np.linspace(0, horizon_days, 401)
    cues = np.linspace(0, 1, 101)
    rate = forward_per_day * cues + reverse_per_day
    equilibrium_curve = np.divide(
        forward_per_day * cues, rate, out=np.zeros_like(cues), where=rate > 0
    )
    return {
        "days": days,
        "fraction": well_mixed_fraction(
            forward_per_day, reverse_per_day, cue, days, initial_fraction
        ),
        "scaled_fraction": well_mixed_fraction(
            rate_scale * forward_per_day, rate_scale * reverse_per_day, cue, days, initial_fraction
        ),
        "landmarks": niche_landmarks(forward_per_day, reverse_per_day, cue),
        "scaled_landmarks": niche_landmarks(
            rate_scale * forward_per_day, rate_scale * reverse_per_day, cue
        ),
        "cues": cues,
        "equilibrium_curve": equilibrium_curve,
        "parameters": {
            "forward_per_day": forward_per_day,
            "reverse_per_day": reverse_per_day,
            "cue": cue,
            "initial_fraction": initial_fraction,
            "rate_scale": rate_scale,
        },
    }


def draw_well_mixed(figure, run):
    figure.clear()
    course, curve = figure.subplots(1, 2, gridspec_kw={"width_ratios": [1.5, 1]})
    p, marks, scaled = run["parameters"], run["landmarks"], run["scaled_landmarks"]
    course.plot(
        run["days"],
        run["fraction"],
        color="#31858f",
        lw=2,
        label=f"k_f = {p['forward_per_day']:g}, k_r = {p['reverse_per_day']:g} /day",
    )
    course.plot(
        run["days"],
        run["scaled_fraction"],
        color="#d67645",
        ls="--",
        lw=2,
        label=f"Both rates × {p['rate_scale']:g}",
    )
    if np.isfinite(marks["equilibrium_fraction"]):
        course.axhline(
            marks["equilibrium_fraction"],
            color="black",
            lw=0.8,
            ls=":",
            label=f"Equilibrium m* = {marks['equilibrium_fraction']:.2f}",
        )
    for landmark, colour in ((marks, "#31858f"), (scaled, "#d67645")):
        tau = landmark["time_constant_days"]
        if np.isfinite(tau) and tau <= run["days"][-1]:
            course.axvline(tau, color=colour, lw=0.8, alpha=0.6)
    course.set(
        xlabel="Elapsed time (days)",
        ylabel="MES-like fraction M/(P+M)",
        ylim=(0, 1),
        title=f"Well-mixed, cue s = {p['cue']:g}; vertical lines at 1/(k_f s + k_r)",
    )
    course.legend(fontsize=8, loc="best")
    curve.plot(run["cues"], run["equilibrium_curve"], color="#31858f")
    if np.isfinite(marks["equilibrium_fraction"]):
        curve.plot([p["cue"]], [marks["equilibrium_fraction"]], "o", color="black")
    curve.set(
        xlabel="Cue s (dimensionless)",
        ylabel="Equilibrium fraction m*",
        ylim=(0, 1),
        title="Equilibrium depends on k_f/k_r only",
    )
    figure.suptitle("Synthetic two-state composition model; no cell growth or death")
    figure.tight_layout()


def well_mixed_explorer():
    """Sliders for both rates, the cue, the initial fraction and a common rate factor."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    controls = _sliders(
        widgets,
        {
            "forward_per_day": (0.08, 0.0, 0.3, 0.01, "k_f forward (1/day)"),
            "reverse_per_day": (0.02, 0.0, 0.1, 0.005, "k_r reverse (1/day)"),
            "cue": (1.0, 0.0, 1.0, 0.05, "Cue s"),
            "initial_fraction": (0.1, 0.0, 1.0, 0.05, "Initial fraction m0"),
            "rate_scale": (2.0, 0.25, 4.0, 0.25, "Common rate factor"),
        },
    )

    def show(**values):
        figure = plt.figure(figsize=(12, 4.2))
        draw_well_mixed(figure, well_mixed_scenario(**values))
        show_figure(figure)

    return _panel(widgets, controls, show)


def niche_fields(cue_amplitude: float = 1.0, cue_x_mm: float = 7.0, cue_width_mm: float = 8.0):
    """Total abundance (as in niche_example) and a Gaussian cue on the constructed plane."""
    x, y = np.meshgrid(GRID_MM, GRID_MM, indexing="ij")
    total = 0.7 * np.exp(-(x**2 + y**2) / (2 * 9**2))
    cue = cue_amplitude * np.exp(-((x - cue_x_mm) ** 2 + y**2) / (2 * cue_width_mm**2))
    return total, cue


def niche_scenario(
    forward_per_day: float = 0.08,
    reverse_per_day: float = 0.02,
    cue_amplitude: float = 1.0,
    cue_x_mm: float = 7.0,
    cue_width_mm: float = 8.0,
    day: float = 10.0,
    horizon_days: float = 60.0,
    initial_fraction: float = 0.1,
) -> dict:
    """Spatial composition at one day and the overall fraction over time."""
    total, cue = niche_fields(cue_amplitude, cue_x_mm, cue_width_mm)
    other, mes = (1 - initial_fraction) * total, initial_fraction * total
    days = np.linspace(0, horizon_days, 121)

    def overall(signal, elapsed):
        return float(
            niche_transition(other, mes, signal, forward_per_day, reverse_per_day, elapsed)[1].sum()
            / total.sum()
        )

    zero = np.zeros_like(cue)
    final_other, final_mes = niche_transition(
        other, mes, cue, forward_per_day, reverse_per_day, day
    )
    rate = forward_per_day * cue + reverse_per_day
    local_equilibrium = np.divide(
        forward_per_day * cue, rate, out=np.zeros_like(cue), where=rate > 0
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        fraction_map = np.where(total > 1e-3, final_mes / total, np.nan)
    return {
        "total": total,
        "cue": cue,
        "fraction_map": fraction_map,
        "days": days,
        "overall": np.array([overall(cue, t) for t in days]),
        "overall_no_cue": np.array([overall(zero, t) for t in days]),
        "long_run_overall": float((total * local_equilibrium).sum() / total.sum())
        if reverse_per_day > 0
        else np.nan,
        "total_change_max_abs": float(np.max(np.abs(final_other + final_mes - total))),
        "parameters": {
            "forward_per_day": forward_per_day,
            "reverse_per_day": reverse_per_day,
            "cue_amplitude": cue_amplitude,
            "cue_x_mm": cue_x_mm,
            "cue_width_mm": cue_width_mm,
            "day": day,
            "initial_fraction": initial_fraction,
        },
    }


def draw_niche_state(figure, run):
    figure.clear()
    cue_axis, map_axis, course = figure.subplots(1, 3)
    p = run["parameters"]
    image = cue_axis.imshow(
        run["cue"].T, origin="lower", extent=EXTENT_MM, vmin=0, vmax=1, cmap="Greens"
    )
    cue_axis.contour(
        GRID_MM, GRID_MM, run["total"].T, levels=[0.1, 0.35, 0.6], colors="black", linewidths=0.7
    )
    cue_axis.set(
        title="Cue s (green), total abundance contours",
        xlabel="Constructed x (mm)",
        ylabel="Constructed y (mm)",
    )
    figure.colorbar(image, ax=cue_axis, shrink=0.75).set_label("Cue (dimensionless)")
    image = map_axis.imshow(
        run["fraction_map"].T, origin="lower", extent=EXTENT_MM, vmin=0, vmax=1, cmap="viridis"
    )
    map_axis.set(title=f"MES-like fraction on day {p['day']:g}", xlabel="Constructed x (mm)")
    figure.colorbar(image, ax=map_axis, shrink=0.75).set_label("M/(P+M)")
    course.plot(run["days"], run["overall"], color="#31858f", label="With cue")
    course.plot(run["days"], run["overall_no_cue"], color="#555555", label="No cue")
    if np.isfinite(run["long_run_overall"]):
        course.axhline(
            run["long_run_overall"],
            color="#31858f",
            ls=":",
            lw=0.9,
            label=f"Long-run limit {run['long_run_overall']:.2f}",
        )
    course.axvline(p["day"], color="black", lw=0.8)
    course.set(
        xlabel="Elapsed time (days)",
        ylabel="Overall MES-like fraction",
        ylim=(0, 1),
        title=f"Total unchanged (max |Δ| = {run['total_change_max_abs']:.0e})",
    )
    course.legend(fontsize=8)
    figure.suptitle(
        f"Synthetic niche: k_f = {p['forward_per_day']:g}/day, k_r = {p['reverse_per_day']:g}/day,"
        f" cue amplitude {p['cue_amplitude']:g} at x = {p['cue_x_mm']:g} mm,"
        f" width {p['cue_width_mm']:g} mm"
    )
    figure.tight_layout()


def niche_explorer():
    """Sliders for the rates, cue amplitude, position and width, and the displayed day."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    controls = _sliders(
        widgets,
        {
            "forward_per_day": (0.08, 0.0, 0.3, 0.01, "k_f forward (1/day)"),
            "reverse_per_day": (0.02, 0.0, 0.1, 0.005, "k_r reverse (1/day)"),
            "cue_amplitude": (1.0, 0.0, 1.0, 0.05, "Cue amplitude"),
            "cue_x_mm": (7.0, -20.0, 20.0, 1.0, "Cue centre x (mm)"),
            "cue_width_mm": (8.0, 2.0, 20.0, 1.0, "Cue width σ (mm)"),
            "day": (10.0, 0.0, 60.0, 1.0, "Displayed day"),
        },
    )

    def show(**values):
        figure = plt.figure(figsize=(14, 4.2))
        draw_niche_state(figure, niche_scenario(**values))
        show_figure(figure)

    return _panel(widgets, controls, show)


# --- Notebook 06: neuron-glioma feedback ------------------------------------------------


def logistic_density(initial: float, rate_per_day: float, days) -> np.ndarray:
    """Exact logistic solution c0 e^{rt} / (1 - c0 + c0 e^{rt})."""
    growth = np.exp(rate_per_day * np.asarray(days, dtype=float))
    return initial * growth / (1 - initial + initial * growth)


def signal_nullcline(density, drive: float, beta_per_day: float, tau_days: float) -> np.ndarray:
    """Signal level where da/dt = 0: a = (b/tau + beta c) / (1/tau + beta c)."""
    density = np.asarray(density, dtype=float)
    return (drive / tau_days + beta_per_day * density) / (1 / tau_days + beta_per_day * density)


def feedback_scenario(
    kappa: float = 1.5,
    beta_per_day: float = 0.12,
    drive: float = 0.3,
    tau_days: float = 4.0,
    initial_density: float = 0.05,
    rho_per_day: float = 0.04,
    horizon_days: float = 150.0,
    dt_days: float = 0.1,
) -> dict:
    """Well-mixed baseline, one-way and feedback runs; the signal starts at the drive."""
    base = NeuronGliomaParameters(
        proliferation_per_day=rho_per_day,
        signal_growth_coupling=kappa,
        tumor_signal_feedback_per_day=beta_per_day,
        signal_relaxation_days=tau_days,
    )
    cases = {
        "baseline": replace(base, signal_growth_coupling=0, tumor_signal_feedback_per_day=0),
        "one_way": replace(base, tumor_signal_feedback_per_day=0),
        "feedback": base,
    }
    steps = int(round(horizon_days / dt_days))
    runs = {
        key: well_mixed_neuron_glioma(initial_density, drive, drive, params, dt_days, steps)
        for key, params in cases.items()
    }
    days = runs["baseline"]["time_days"]
    effective_rate = rho_per_day * (1 + kappa * drive)
    return {
        "runs": runs,
        "effective_rate_per_day": effective_rate,
        "effective_logistic": logistic_density(initial_density, effective_rate, days),
        "parameters": {
            "kappa": kappa,
            "beta_per_day": beta_per_day,
            "drive": drive,
            "tau_days": tau_days,
            "initial_density": initial_density,
            "rho_per_day": rho_per_day,
        },
    }


def draw_feedback_state(figure, run):
    figure.clear()
    density_axis, signal_axis, phase = figure.subplots(1, 3)
    p = run["parameters"]
    for key, values in run["runs"].items():
        density_axis.plot(
            values["time_days"], values["density"], color=CASE_COLOURS[key], label=CASE_LABELS[key]
        )
        signal_axis.plot(values["time_days"], values["signal"], color=CASE_COLOURS[key])
    days = run["runs"]["baseline"]["time_days"]
    density_axis.plot(
        days,
        run["effective_logistic"],
        color="black",
        ls=":",
        lw=1.5,
        label=f"Logistic, ρ_eff = ρ(1+κb) = {run['effective_rate_per_day']:.3f}/day",
    )
    density_axis.set(
        xlabel="Elapsed time (days)",
        ylabel="Normalized density c",
        ylim=(0, 1.02),
        title="Density: one-way equals a faster baseline",
    )
    density_axis.legend(fontsize=7.5, loc="lower right")
    signal_axis.set(
        xlabel="Elapsed time (days)",
        ylabel="Signal index a",
        ylim=(0, 1.02),
        title="Signal: only feedback moves it",
    )
    c_grid, a_grid = np.meshgrid(np.linspace(0.02, 0.98, 13), np.linspace(0.02, 0.98, 13))
    dc = p["rho_per_day"] * (1 + p["kappa"] * a_grid) * c_grid * (1 - c_grid)
    da = (p["drive"] - a_grid) / p["tau_days"] + p["beta_per_day"] * c_grid * (1 - a_grid)
    speed = np.hypot(dc, da)
    phase.quiver(
        c_grid,
        a_grid,
        dc / (speed + 1e-12),
        da / (speed + 1e-12),
        color="#bbbbbb",
        scale=28,
        width=0.004,
    )
    c_line = np.linspace(0, 1, 101)
    phase.plot(
        c_line,
        signal_nullcline(c_line, p["drive"], p["beta_per_day"], p["tau_days"]),
        color="black",
        ls="--",
        lw=1,
        label="Signal nullcline (da/dt = 0)",
    )
    feedback = run["runs"]["feedback"]
    phase.plot(
        feedback["density"],
        feedback["signal"],
        color=CASE_COLOURS["feedback"],
        lw=2,
        label="Feedback trajectory",
    )
    phase.plot(feedback["density"][0], feedback["signal"][0], "o", color="black")
    phase.set(
        xlabel="Normalized density c",
        ylabel="Signal index a",
        xlim=(0, 1),
        ylim=(0, 1),
        title="Phase plane (arrows: direction only)",
    )
    phase.legend(fontsize=7.5, loc="lower right")
    figure.suptitle(
        f"Synthetic well-mixed model: κ = {p['kappa']:g}, β = {p['beta_per_day']:g}/day, "
        f"drive b = {p['drive']:g}, τ = {p['tau_days']:g} days, ρ = {p['rho_per_day']:g}/day"
    )
    figure.tight_layout()


def feedback_explorer():
    """Sliders for coupling, feedback, drive, relaxation time and initial density."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    controls = _sliders(
        widgets,
        {
            "kappa": (1.5, 0.0, 3.0, 0.1, "κ signal→growth"),
            "beta_per_day": (0.12, 0.0, 0.5, 0.01, "β tumour→signal (1/day)"),
            "drive": (0.3, 0.0, 1.0, 0.05, "External drive b"),
            "tau_days": (4.0, 0.5, 20.0, 0.5, "Relaxation τ (days)"),
            "initial_density": (0.05, 0.01, 0.5, 0.01, "Initial density c0"),
        },
    )

    def show(**values):
        figure = plt.figure(figsize=(14, 4.3))
        draw_feedback_state(figure, feedback_scenario(**values))
        show_figure(figure)

    return _panel(widgets, controls, show)


@lru_cache(maxsize=32)
def _spatial_runs(kappa, beta, amplitude, drive_x, steps):
    x, y = np.meshgrid(GRID_MM, GRID_MM, indexing="ij")
    initial = 0.35 * np.exp(-((x + 5) ** 2 + y**2) / (2 * 4**2))
    drive = 0.1 + amplitude * np.exp(-((x - drive_x) ** 2 + (y - 2) ** 2) / (2 * 7**2))
    base = NeuronGliomaParameters(signal_growth_coupling=kappa, tumor_signal_feedback_per_day=beta)
    cases = {
        "baseline": replace(base, signal_growth_coupling=0, tumor_signal_feedback_per_day=0),
        "one_way": replace(base, tumor_signal_feedback_per_day=0),
        "feedback": base,
    }
    runs = {
        key: simulate_neuron_glioma(initial, drive, drive, params, 1, 1, 0.1, steps)
        for key, params in cases.items()
    }
    return initial, drive, runs


def spatial_scenario(
    kappa: float = 1.5,
    beta_per_day: float = 0.12,
    drive_amplitude: float = 0.7,
    drive_x_mm: float = 4.0,
    day: float = 20.0,
) -> dict:
    """The notebook-06 construction with a movable drive; 1 mm grid, 0.1 day steps."""
    if drive_amplitude < 0 or drive_amplitude > 0.9:
        raise ValueError("Drive amplitude must lie in [0, 0.9] so the drive stays below one.")
    steps = max(1, int(round(day / 0.1)))
    initial, drive, runs = _spatial_runs(
        round(kappa, 4),
        round(beta_per_day, 4),
        round(drive_amplitude, 4),
        round(drive_x_mm, 4),
        steps,
    )
    return {
        "initial": initial,
        "drive": drive,
        "runs": runs,
        "parameters": {
            "kappa": kappa,
            "beta_per_day": beta_per_day,
            "drive_amplitude": drive_amplitude,
            "drive_x_mm": drive_x_mm,
            "day": steps * 0.1,
        },
    }


def draw_spatial_state(figure, run):
    figure.clear()
    density_axis, signal_axis, trace = figure.subplots(1, 3)
    p, runs = run["parameters"], run["runs"]
    image = density_axis.imshow(
        runs["feedback"]["density"].T,
        origin="lower",
        extent=EXTENT_MM,
        vmin=0,
        vmax=1,
        cmap="magma",
    )
    density_axis.contour(
        GRID_MM,
        GRID_MM,
        runs["baseline"]["density"].T,
        levels=[0.1],
        colors="white",
        linewidths=1,
        linestyles="--",
    )
    density_axis.contour(
        GRID_MM, GRID_MM, run["drive"].T, levels=[0.3, 0.6], colors="#7fd3dc", linewidths=0.9
    )
    density_axis.set(
        xlim=(-20, 20),
        ylim=(-20, 20),
        xlabel="Constructed x (mm)",
        ylabel="Constructed y (mm)",
        title="Feedback density; dashed: baseline c = 0.1",
    )
    figure.colorbar(image, ax=density_axis, shrink=0.75).set_label("Normalized density")
    image = signal_axis.imshow(
        (runs["feedback"]["signal"] - run["drive"]).T,
        origin="lower",
        extent=EXTENT_MM,
        vmin=0,
        vmax=0.3,
        cmap="viridis",
    )
    signal_axis.set(
        xlim=(-20, 20),
        ylim=(-20, 20),
        xlabel="Constructed x (mm)",
        title="Signal raised by feedback (a − b)",
    )
    figure.colorbar(image, ax=signal_axis, shrink=0.75).set_label("Signal index change")
    for key, values in runs.items():
        trace.plot(
            values["time_days"],
            values["density_integral_mm2"],
            color=CASE_COLOURS[key],
            label=CASE_LABELS[key],
        )
    trace.set(
        xlabel="Elapsed time (days)",
        ylabel="Density integral (mm²)",
        title="Three nested assumptions",
    )
    trace.legend(fontsize=8)
    figure.suptitle(
        f"Synthetic plane, day {p['day']:g}: κ = {p['kappa']:g}, β = {p['beta_per_day']:g}/day, "
        f"drive amplitude {p['drive_amplitude']:g} centred at x = {p['drive_x_mm']:g} mm "
        "(cyan contours)"
    )
    figure.tight_layout()


def spatial_explorer():
    """Sliders for coupling, feedback, drive amplitude and position, and the day."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    controls = _sliders(
        widgets,
        {
            "kappa": (1.5, 0.0, 3.0, 0.25, "κ signal→growth"),
            "beta_per_day": (0.12, 0.0, 0.4, 0.02, "β tumour→signal (1/day)"),
            "drive_amplitude": (0.7, 0.0, 0.9, 0.05, "Drive amplitude"),
            "drive_x_mm": (4.0, -15.0, 15.0, 1.0, "Drive centre x (mm)"),
            "day": (20.0, 2.0, 40.0, 2.0, "Day"),
        },
    )

    def show(**values):
        figure = plt.figure(figsize=(14, 4.3))
        draw_spatial_state(figure, spatial_scenario(**values))
        show_figure(figure)

    return _panel(widgets, controls, show)
