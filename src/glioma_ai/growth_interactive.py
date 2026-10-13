"""Interactive explorers for notebook 02; rendering is separate from widgets.

The draw_* functions take precomputed runs and work with any Matplotlib
backend, so they are tested without ipywidgets. The explorers import
ipywidgets lazily (notebooks dependency group) and re-solve the prescribed
model when a coefficient changes; moving the day slider only selects a snapshot.
"""

import time
from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D

from glioma_ai.growth_model import DensityRun, diffusion_step_limit, simulate_density_2d
from glioma_ai.tissue_growth import (
    CSF,
    INFERIOR_SUPERIOR,
    LEFT_RIGHT,
    OUTSIDE,
    WHITE,
    CoronalPhantom,
    contralateral_summary,
    coronal_phantom,
    tissue_scenarios,
)

DISK_COORDINATES = np.arange(121, dtype=float) - 60
DISK_EXTENT = (-60.5, 60.5, -60.5, 60.5)
DISK_DAYS = np.arange(0, 101, 2, dtype=float)
TISSUE_DAYS = np.arange(0, 366, 5, dtype=float)
TISSUE_COLOURS = ListedColormap(["white", "#9ecae1", "#9a9a9a", "#e6e6e6"])
SCENARIO_COLOURS = ("#7f7f7f", "#1f77b4", "#d62728")


def disk_seed() -> np.ndarray:
    x, y = np.meshgrid(DISK_COORDINATES, DISK_COORDINATES, indexing="ij")
    return 0.65 * (x * x + y * y <= 7**2)


def disk_run(d_mm2_per_day: float, rho_per_day: float) -> DensityRun:
    """Figure 1 seed on a wider 121 x 121 mm plane; dt is 0.9 of the bound, at most 0.2 day."""
    limit = diffusion_step_limit(d_mm2_per_day, 1.0, 1.0)
    return simulate_density_2d(
        disk_seed(), d_mm2_per_day, rho_per_day, DISK_DAYS, dt_days=min(0.2, 0.9 * limit)
    )


def draw_disk_state(
    figure, run: DensityRun, day: float, threshold: float, d: float, rho: float
) -> None:
    """Density at one day plus M(t) and A_theta(t) with the day marked."""
    index = int(np.argmin(np.abs(run.days - day)))
    axes = figure.subplots(1, 3, gridspec_kw={"width_ratios": [1.15, 1, 1]})
    image = axes[0].imshow(
        run.density[index].T, origin="lower", extent=DISK_EXTENT, cmap="magma", vmin=0, vmax=1
    )
    field = run.density[index].T
    for level, colour in ((0.1, "#84dfdb"), (threshold, "white")):
        if field.min() < level < field.max():
            axes[0].contour(DISK_COORDINATES, DISK_COORDINATES, field, [level], colors=colour)
    axes[0].set_title(f"Density proxy c, t = {run.days[index]:g} days", loc="left")
    axes[0].set_xlabel("Synthetic x (mm)")
    axes[0].set_ylabel("Synthetic y (mm)")
    axes[0].legend(
        handles=[
            Line2D([], [], color="#84dfdb", label="c = 0.1"),
            Line2D([], [], color="white", label=f"c = {threshold:g} (θ)"),
        ],
        loc="lower left",
        fontsize=8,
        facecolor="#333333",
        labelcolor="white",
    )
    figure.colorbar(image, ax=axes[0], shrink=0.8, label="Normalized density proxy c")
    axes[1].plot(run.days, run.integral_mm2, color="#2ca02c")
    axes[1].set_ylabel("M = ∫c dA (mm²); not a cell count")
    axes[1].set_title("Integrated density proxy", loc="left")
    axes[2].plot(run.days, run.areas_mm2(threshold), color="#d62728", label=f"θ = {threshold:g}")
    axes[2].plot(run.days, run.areas_mm2(0.1), color="#1f77b4", ls="--", label="θ = 0.1")
    axes[2].set_ylabel("Area at c ≥ θ (mm²)")
    axes[2].set_title("Thresholded area", loc="left")
    axes[2].legend(fontsize=8)
    for axis in axes[1:]:
        axis.axvline(run.days[index], color="black", lw=0.8, ls=":")
        axis.set_xlabel("Elapsed model time (days)")
    walls = run.density.copy()
    walls[:, 1:-1, 1:-1] = 0
    touched = walls.max(axis=(1, 2)) >= 0.01
    warning = (
        f"\nWarning: c ≥ 0.01 reaches the outer no-flux wall from day "
        f"{run.days[np.argmax(touched)]:g}; values after that are affected by the wall."
        if touched.any()
        else ""
    )
    speed = 2 * np.sqrt(d * rho)
    scale = f"ℓ = √(D/ρ) = {np.sqrt(d / rho):.1f} mm" if rho > 0 else "ℓ undefined (ρ = 0)"
    figure.suptitle(
        f"Synthetic disk, D = {d:g} mm²/day, ρ = {rho:g}/day:  {scale};  "
        f"v* = 2√(Dρ) = {speed:.2f} mm/day;  step {run.largest_step_days:.3g} day "
        f"({run.n_steps} steps){warning}",
        fontsize=10,
    )


def draw_tissue_map(axis, phantom: CoronalPhantom, *, glyph_every_mm: float = 6.0) -> None:
    """Tissue classes with fibre glyphs and radiological L/R labels."""
    axis.imshow(
        phantom.tissue.T,
        origin="lower",
        extent=phantom.extent,
        cmap=TISSUE_COLOURS,
        vmin=OUTSIDE - 0.5,
        vmax=WHITE + 0.5,
        interpolation="nearest",
    )
    step = max(1, int(round(glyph_every_mm / phantom.spacing_mm)))
    half = 0.4 * glyph_every_mm
    for i in range(0, len(phantom.x_mm), step):
        for j in range(0, len(phantom.y_mm), step):
            x, y, kind = phantom.x_mm[i], phantom.y_mm[j], phantom.fibre[i, j]
            if kind == LEFT_RIGHT:
                axis.plot([x - half, x + half], [y, y], color="#b8860b", lw=1.2)
            elif kind == INFERIOR_SUPERIOR:
                axis.plot([x, x], [y - half, y + half], color="#6a3d9a", lw=1.0)
    label_axes(axis, phantom)


def label_axes(axis, phantom: CoronalPhantom) -> None:
    axis.set_xlabel("x (mm): patient right ← → patient left")
    axis.set_ylabel("y (mm): inferior → superior")
    for x, text in ((phantom.x_mm[0] + 4, "R"), (phantom.x_mm[-1] - 4, "L")):
        axis.text(x, phantom.y_mm[-1] - 6, text, fontsize=12, weight="bold", ha="center")


def draw_density_on_tissue(axis, phantom: CoronalPhantom, density: np.ndarray, *, alpha=1.0):
    axis.imshow(
        phantom.tissue.T,
        origin="lower",
        extent=phantom.extent,
        cmap=TISSUE_COLOURS,
        vmin=OUTSIDE - 0.5,
        vmax=WHITE + 0.5,
        interpolation="nearest",
    )
    image = axis.imshow(
        np.ma.masked_less(density.T, 0.01),
        origin="lower",
        extent=phantom.extent,
        cmap="magma",
        vmin=0,
        vmax=1,
        alpha=alpha,
    )
    for level, colour in ((0.1, "#00a0c8"), (0.5, "black")):
        if density.min() < level < density.max():
            axis.contour(
                phantom.x_mm, phantom.y_mm, density.T, [level], colors=colour, linewidths=1
            )
    axis.contour(
        phantom.x_mm,
        phantom.y_mm,
        (phantom.tissue == CSF).T.astype(float),
        [0.5],
        colors="#4a90c2",
        linewidths=0.5,
    )
    label_axes(axis, phantom)
    return image


def tissue_legend_handles() -> list:
    from matplotlib.patches import Patch

    return [
        Patch(color="#9ecae1", label="CSF (D = 0, ρ = 0)"),
        Patch(color="#9a9a9a", label="Grey matter"),
        Patch(color="#e6e6e6", label="White matter"),
        Line2D([], [], color="#b8860b", label="left–right fibres"),
        Line2D([], [], color="#6a3d9a", label="inferior–superior fibres"),
    ]


def draw_tissue_state(figure, phantom: CoronalPhantom, runs: dict, day: float) -> None:
    """Fibre-guided state, uniform-tissue state, and contralateral fraction over time."""
    names = list(runs)
    guided, uniform = runs[names[-1]][0], runs[names[0]][0]
    index = int(np.argmin(np.abs(guided.days - day)))
    axes = figure.subplots(1, 3, gridspec_kw={"width_ratios": [1, 1, 0.9]})
    image = draw_density_on_tissue(axes[0], phantom, guided.density[index])
    axes[0].set_title(f"Tissue-guided, t = {guided.days[index]:g} days", loc="left")
    draw_density_on_tissue(axes[1], phantom, uniform.density[index])
    axes[1].set_title(f"Uniform tissue, t = {uniform.days[index]:g} days", loc="left")
    figure.colorbar(image, ax=axes[:2], shrink=0.7, label="Normalized density proxy c")
    for name, colour in zip(names, SCENARIO_COLOURS, strict=True):
        run = runs[name][0]
        summary = contralateral_summary(phantom, run)
        first = summary["first_day_at_threshold"]
        reached = "not reached" if first is None else f"day {first:g}"
        label = f"{name}\n(c ≥ 0.1 across midline: {reached})"
        axes[2].plot(run.days, 100 * summary["contralateral_fraction"], color=colour, label=label)
    axes[2].axvline(guided.days[index], color="black", lw=0.8, ls=":")
    axes[2].set_xlabel("Elapsed model time (days)")
    axes[2].set_ylabel("Share of M in patient-right hemisphere (%)")
    axes[2].set_title("Contralateral share of the density proxy", loc="left")
    axes[2].legend(fontsize=7, loc="upper left")


@lru_cache(maxsize=16)
def _cached_disk(d: float, rho: float) -> DensityRun:
    return disk_run(d, rho)


@lru_cache(maxsize=8)
def _cached_tissue(d_g: float, ratio: float, fibre: float, rho: float):
    phantom = coronal_phantom()
    started = time.perf_counter()
    runs = tissue_scenarios(
        phantom,
        grey_mm2_per_day=d_g,
        white_to_grey=ratio,
        fibre_ratio=fibre,
        rho_per_day=rho,
        days=TISSUE_DAYS,
    )
    return phantom, runs, time.perf_counter() - started


def _with_player(widgets, controls: dict, show, *, interval_ms: int):
    """Sliders plus a play button stepping the day slider; each step redraws the figure."""
    from glioma_ai.notebook_display import play_control

    day = controls["day"]
    player, player_box = play_control(
        widgets,
        value=day.value,
        min=day.min,
        max=day.max,
        step=day.step,
        interval=interval_ms,
        description="Play days",
        layout=widgets.Layout(width="auto"),
    )
    widgets.jslink((player, "value"), (day, "value"))
    rows = [widgets.HBox([day, player_box]) if c is day else c for c in controls.values()]
    output = widgets.interactive_output(show, controls)
    return widgets.VBox([widgets.VBox(rows), output])


def isotropic_explorer():
    """Sliders for D, rho, observation day and display threshold (Figure 1 set-up)."""
    import ipywidgets as widgets
    from IPython.display import display

    style = {"description_width": "11em"}
    layout = widgets.Layout(width="34em")
    controls = {
        "d": widgets.FloatSlider(0.35, min=0.0, max=1.5, step=0.05, description="D (mm²/day)"),
        "rho": widgets.FloatSlider(
            0.035, min=0.0, max=0.1, step=0.005, description="ρ (1/day)", readout_format=".3f"
        ),
        "day": widgets.IntSlider(
            28, min=0, max=int(DISK_DAYS[-1]), step=2, description="Observation day"
        ),
        "threshold": widgets.FloatSlider(
            0.5, min=0.05, max=0.95, step=0.05, description="Display threshold θ"
        ),
    }
    for control in controls.values():
        control.style, control.layout, control.continuous_update = style, layout, False

    def show(d, rho, day, threshold):
        run = _cached_disk(round(d, 4), round(rho, 4))
        figure = plt.figure(figsize=(14, 4.4), constrained_layout=True)
        draw_disk_state(figure, run, day, threshold, d, rho)
        plt.show()

    display(_with_player(widgets, controls, show, interval_ms=700))


def tissue_explorer():
    """Sliders for grey-matter D, white/grey ratio, fibre ratio, rho and day (Figure 2)."""
    import ipywidgets as widgets
    from IPython.display import display

    style = {"description_width": "15em"}
    layout = widgets.Layout(width="38em")
    controls = {
        "d_g": widgets.FloatSlider(
            0.1, min=0.02, max=0.2, step=0.01, description="Grey-matter D_g (mm²/day)"
        ),
        "ratio": widgets.FloatSlider(
            5.0, min=1.0, max=8.0, step=0.5, description="White/grey ratio r"
        ),
        "fibre": widgets.FloatSlider(
            2.0, min=1.0, max=4.0, step=0.5, description="Along-fibre factor a"
        ),
        "rho": widgets.FloatSlider(
            0.035, min=0.005, max=0.08, step=0.005, description="ρ (1/day)", readout_format=".3f"
        ),
        "day": widgets.IntSlider(
            240, min=0, max=int(TISSUE_DAYS[-1]), step=5, description="Observation day"
        ),
    }
    for control in controls.values():
        control.style, control.layout, control.continuous_update = style, layout, False

    def show(d_g, ratio, fibre, rho, day):
        phantom, runs, seconds = _cached_tissue(
            round(d_g, 4), round(ratio, 4), round(fibre, 4), round(rho, 4)
        )
        guided = runs[list(runs)[-1]][0]
        figure = plt.figure(figsize=(15, 4.8), constrained_layout=True)
        draw_tissue_state(figure, phantom, runs, day)
        figure.suptitle(
            f"Constructed coronal phantom: D_g = {d_g:g}, D_w = {ratio * d_g:g}, along fibres "
            f"{fibre * ratio * d_g:g} mm²/day; ρ = {rho:g}/day.  Tissue-guided step "
            f"{guided.largest_step_days:.3g} day ({guided.n_steps} steps); "
            f"three runs solved in {seconds:.1f} s",
            fontsize=10,
        )
        plt.show()

    display(_with_player(widgets, controls, show, interval_ms=900))
