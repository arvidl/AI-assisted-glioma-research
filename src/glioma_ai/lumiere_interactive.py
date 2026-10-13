"""What-if explorer for notebook 03; computation and drawing are separate from widgets.

``what_if_run`` and ``draw_what_if`` work without ipywidgets and are tested.
The explorer imports ipywidgets lazily (notebooks dependency group) and
re-solves the two-level model when a setting changes; moving the day slider only
selects a snapshot. Only day 28 has an observed scan; other days are projections
of the stated assumptions, not predictions.
"""

from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from glioma_ai.growth_model import DensityRun, simulate_density_2d
from glioma_ai.lumiere_biology import (
    FORMER_DEFAULTS,
    LITERATURE,
    T1GD_FRACTION,
    T2_FRACTION,
    WHOLE_LABELS,
    brain_domain,
    front_speed_mm_per_day,
    front_width_mm,
    local_and_distant,
    score_density,
)
from glioma_ai.lumiere_dynamics import CORE_LABELS, SliceCase, _extent, prepare_slice_case

HORIZON_DAYS = 112
SNAPSHOT_DAYS = np.arange(0, HORIZON_DAYS + 1, 4, dtype=float)
OBSERVED_DAY = 28
INITIAL_VISIT, LATER_VISIT = "week-045", "week-049"
DEFAULTS = {
    "diffusivity_mm2_per_day": LITERATURE["diffusivity_mm2_per_day"],
    "rho_per_day": LITERATURE["rho_per_day"],
    "core_level": 0.9,
    "margin_level": 0.36,
    "core_threshold": T1GD_FRACTION,
    "t2_threshold": T2_FRACTION,
    "abnormal_factor": 1.0,
    "boundary_shift_mm": 0,
    "use_brain_domain": True,
}


def shift_mask(mask: np.ndarray, cells: int) -> np.ndarray:
    """Grow (cells > 0) or shrink (cells < 0) a 2D mask by 4-neighbour steps.

    A crude, explicit model of label-boundary uncertainty; not a re-segmentation.
    """
    out = np.asarray(mask, dtype=bool).copy()
    for _ in range(abs(int(cells))):
        padded = np.pad(out, 1, constant_values=cells < 0)
        neighbours = (padded[:-2, 1:-1], padded[2:, 1:-1], padded[1:-1, :-2], padded[1:-1, 2:])
        if cells > 0:
            out = out | np.logical_or.reduce(neighbours)
        else:
            out = out & np.logical_and.reduce(neighbours)
    return out


def check_settings(settings: dict) -> str | None:
    """A readable reason why a combination is invalid, or None."""
    core_t, t2_t = settings["core_threshold"], settings["t2_threshold"]
    if not 0 < t2_t < core_t < 1:
        return "Require 0 < T2/FLAIR threshold < core threshold < 1."
    if not core_t <= settings["core_level"] <= 1:
        return "The starting core density must be at least the core threshold."
    if not t2_t <= settings["margin_level"] < core_t:
        return "The starting margin density must lie between the two thresholds."
    return None


def what_if_run(case: SliceCase, days: np.ndarray = SNAPSHOT_DAYS, **overrides) -> dict:
    """Two-level run from week 045 with explicit what-if settings.

    ``days`` are the snapshot days (default every 4 days to HORIZON_DAYS); they
    must include the observed day 28.
    """
    days = np.asarray(days, dtype=float)
    if OBSERVED_DAY not in days:
        raise ValueError(f"Snapshot days must include the observed day {OBSERVED_DAY}.")
    settings = {**DEFAULTS, **overrides}
    problem = check_settings(settings)
    if problem:
        raise ValueError(problem)
    shift = int(settings["boundary_shift_mm"] / case.dx_mm)
    core = shift_mask(case.roi(INITIAL_VISIT, CORE_LABELS), shift)
    whole = shift_mask(case.roi(INITIAL_VISIT, WHOLE_LABELS), shift) | core
    domain, added = brain_domain(case, INITIAL_VISIT)
    if settings["use_brain_domain"]:
        core, whole = core & domain, whole & domain
    else:
        domain = None
    initial = np.where(core, settings["core_level"], np.where(whole, settings["margin_level"], 0.0))
    d = settings["diffusivity_mm2_per_day"]
    diffusivity = np.where(whole, d * settings["abnormal_factor"], d)
    fastest = max(float(diffusivity.max()), 1e-12)
    dt = min(0.2, 0.9 / (2 * fastest * (case.dx_mm**-2 + case.dy_mm**-2)))
    run: DensityRun = simulate_density_2d(
        initial,
        diffusivity,
        settings["rho_per_day"],
        days,
        dx_mm=case.dx_mm,
        dy_mm=case.dy_mm,
        dt_days=dt,
        domain=domain,
    )
    split = local_and_distant(case, INITIAL_VISIT, LATER_VISIT)
    pixel = case.dx_mm * case.dy_mm
    thresholds = {
        "core_threshold": settings["core_threshold"],
        "t2_threshold": settings["t2_threshold"],
    }
    observed_index = int(np.flatnonzero(days == OBSERVED_DAY)[0])
    return {
        "settings": settings,
        "run": run,
        "split": split,
        "domain": domain,
        "labelled_cells_added_to_domain": added,
        "at_observed_day": score_density(run.density[observed_index], split, pixel, **thresholds),
        "no_change": score_density(initial, split, pixel, **thresholds),
        "core_area_mm2": (run.density >= settings["core_threshold"]).sum(axis=(1, 2)) * pixel,
        "t2_area_mm2": (run.density >= settings["t2_threshold"]).sum(axis=(1, 2)) * pixel,
        "observed": {
            "start_core_mm2": float(case.roi(INITIAL_VISIT, CORE_LABELS).sum() * pixel),
            "start_t2_mm2": float(case.roi(INITIAL_VISIT, WHOLE_LABELS).sum() * pixel),
            "later_core_mm2": float(case.roi(LATER_VISIT, CORE_LABELS).sum() * pixel),
            "later_t2_mm2": float(case.roi(LATER_VISIT, WHOLE_LABELS).sum() * pixel),
        },
        "front_speed_mm_per_day": front_speed_mm_per_day(d, settings["rho_per_day"]),
        "front_width_mm": front_width_mm(d, settings["rho_per_day"]),
        "time_step_days": run.largest_step_days,
    }


def draw_what_if(figure, case: SliceCase, result: dict, day: float) -> None:
    """Density with readings at ``day``, later labels at day 28, and area curves."""
    settings, run, split = result["settings"], result["run"], result["split"]
    index = int(np.argmin(np.abs(run.days - day)))
    shown = run.days[index]
    extent = _extent(case)
    bbox = np.argwhere((run.density[0] > 0) | split["local_whole"] | split["distant_whole"])
    pad = 25
    xlim = (max(bbox[:, 0].min() - pad, 0) * case.dx_mm, (bbox[:, 0].max() + pad) * case.dx_mm)
    ylim = (max(bbox[:, 1].min() - pad, 0) * case.dy_mm, (bbox[:, 1].max() + pad) * case.dy_mm)
    axes = figure.subplots(1, 2, gridspec_kw={"width_ratios": [1.1, 1]})
    background = case.images[case.metadata["visit_names"].index(INITIAL_VISIT)]
    axes[0].imshow(background.T, origin="lower", extent=extent, cmap="gray")
    image = axes[0].imshow(
        np.ma.masked_less(run.density[index], 0.01).T,
        origin="lower",
        extent=extent,
        cmap="magma",
        vmin=0,
        vmax=1,
        alpha=0.85,
    )
    for level, colour in (
        (settings["core_threshold"], "#f29b38"),
        (settings["t2_threshold"], "#48dbbf"),
    ):
        mask = run.density[index] >= level
        if mask.any():
            axes[0].contour(mask.T, levels=[0.5], extent=extent, colors=colour, linewidths=1.5)
    if shown == OBSERVED_DAY:
        later = (
            (split["local_core"] | split["distant_core"], "#f29b38"),
            (split["local_whole"] | split["distant_whole"], "#48dbbf"),
        )
        for mask, colour in later:
            if mask.any():
                axes[0].contour(
                    mask.T,
                    levels=[0.5],
                    extent=extent,
                    colors=colour,
                    linewidths=1.0,
                    linestyles="dashed",
                )
        caption = f"Day {shown:g}: model (solid) and week-049 labels (dashed)"
    else:
        caption = f"Day {shown:g}: projection only (no scan on this day)"
    if result["domain"] is not None:
        axes[0].contour(
            result["domain"].T, levels=[0.5], extent=extent, colors="#bbbbbb", linewidths=0.6
        )
    axes[0].set_xlim(*xlim)
    axes[0].set_ylim(*ylim)
    axes[0].set_aspect("equal")
    axes[0].set_title(caption, loc="left", fontsize=10)
    axes[0].set_xlabel("Image axis 0 toward R (mm)")
    axes[0].set_ylabel("Image axis 1 toward A (mm)")
    figure.colorbar(image, ax=axes[0], shrink=0.8, label="Normalized density proxy c")
    observed = result["observed"]
    axes[1].plot(run.days, result["core_area_mm2"], color="#f29b38", label="model core reading")
    axes[1].plot(run.days, result["t2_area_mm2"], color="#48dbbf", label="model T2/FLAIR reading")
    for key, colour, marker in (("core", "#f29b38", "o"), ("t2", "#48dbbf", "s")):
        axes[1].plot(
            [0, OBSERVED_DAY],
            [observed[f"start_{key}_mm2"], observed[f"later_{key}_mm2"]],
            ls="none",
            marker=marker,
            color=colour,
            markeredgecolor="black",
        )
    axes[1].axvline(shown, color="black", lw=0.8, ls=":")
    axes[1].axvspan(OBSERVED_DAY, HORIZON_DAYS, color="#eeeeee", zorder=0)
    axes[1].text(
        OBSERVED_DAY + 2,
        0.02,
        "projection: no scans",
        transform=axes[1].get_xaxis_transform(),
        fontsize=8,
    )
    axes[1].set_xlabel("Days after week 045")
    axes[1].set_ylabel("Area on this plane (mm²)")
    axes[1].set_title("Readings over time; markers = automated labels", loc="left", fontsize=10)
    handles = axes[1].get_legend_handles_labels()[0] + [
        Line2D(
            [],
            [],
            ls="none",
            marker="o",
            color="#f29b38",
            markeredgecolor="black",
            label="labelled core (weeks 045, 049)",
        ),
        Line2D(
            [],
            [],
            ls="none",
            marker="s",
            color="#48dbbf",
            markeredgecolor="black",
            label="labelled whole union (weeks 045, 049)",
        ),
    ]
    axes[1].legend(handles=handles, fontsize=8, loc="center left", bbox_to_anchor=(1.02, 0.5))
    score, still = result["at_observed_day"], result["no_change"]
    doubling = np.log(2) / settings["rho_per_day"]
    figure.suptitle(
        f"D = {settings['diffusivity_mm2_per_day']:.3g} mm²/day (×{settings['abnormal_factor']:g} "
        f"in abnormal tissue), ρ = {settings['rho_per_day']:.3g}/day (doubling {doubling:.0f} "
        f"days); front 2√(Dρ) = {result['front_speed_mm_per_day']:.3f} mm/day, margin "
        f"√(D/ρ) = {result['front_width_mm']:.2f} mm\n"
        f"Day 28 vs week-049 local labels: core Dice {score['local_core_dice']:.3f} "
        f"(no change {still['local_core_dice']:.3f}), T2/FLAIR Dice "
        f"{score['local_whole_dice']:.3f} (no change {still['local_whole_dice']:.3f}); "
        f"distant lesion reached {score['distant_whole_reached_mm2']:.0f} of "
        f"{score['distant_whole_area_mm2']:.0f} mm²",
        fontsize=9.5,
    )


@lru_cache(maxsize=12)
def _plane_case(root: str, index: int) -> SliceCase:
    return prepare_slice_case(Path(root), axial_index=index)


def what_if_explorer(case: SliceCase, prepared_root: Path | None = None):
    """Spatial, temporal, tissue and model controls for the two-level LUMIERE model."""
    import ipywidgets as widgets
    from IPython.display import display

    from glioma_ai.notebook_display import figure_widget, play_control

    style = {"description_width": "16em"}
    layout = widgets.Layout(width="40em")

    def slider(kind, value, **kwargs):
        control = kind(value=value, style=style, layout=layout, continuous_update=False, **kwargs)
        return control

    base_index = case.metadata.get("slice_index")
    controls = {
        "plane_offset": slider(
            widgets.IntSlider,
            0,
            min=-10,
            max=10,
            step=1,
            description="Plane offset (mm)",
            disabled=prepared_root is None or base_index is None,
        ),
        "boundary_shift_mm": slider(
            widgets.IntSlider, 0, min=-3, max=3, step=1, description="Label boundary shift (mm)"
        ),
        "day": slider(
            widgets.IntSlider,
            OBSERVED_DAY,
            min=0,
            max=HORIZON_DAYS,
            step=4,
            description="Observation day",
        ),
        "use_brain_domain": widgets.Checkbox(
            value=True, description="Confine spread to the brain", style=style, layout=layout
        ),
        "abnormal_factor": slider(
            widgets.FloatLogSlider,
            1.0,
            base=2,
            min=-2,
            max=2,
            step=0.25,
            description="D factor in T2/FLAIR-abnormal tissue",
        ),
        "diffusivity_mm2_per_day": slider(
            widgets.FloatLogSlider,
            DEFAULTS["diffusivity_mm2_per_day"],
            base=10,
            min=-2,
            max=0,
            step=0.05,
            description="D (mm²/day)",
            readout_format=".3f",
        ),
        "rho_per_day": slider(
            widgets.FloatLogSlider,
            DEFAULTS["rho_per_day"],
            base=10,
            min=-2.1,
            max=-0.5,
            step=0.05,
            description="ρ (1/day)",
            readout_format=".3f",
        ),
        "core_level": slider(
            widgets.FloatSlider, 0.9, min=0.5, max=1.0, step=0.02, description="Start density: core"
        ),
        "margin_level": slider(
            widgets.FloatSlider,
            0.36,
            min=0.05,
            max=0.79,
            step=0.01,
            description="Start density: T2/FLAIR margin",
        ),
        "core_threshold": slider(
            widgets.FloatSlider,
            T1GD_FRACTION,
            min=0.3,
            max=0.95,
            step=0.05,
            description="Reading threshold: core",
        ),
        "t2_threshold": slider(
            widgets.FloatSlider,
            T2_FRACTION,
            min=0.02,
            max=0.5,
            step=0.02,
            description="Reading threshold: T2/FLAIR",
        ),
    }
    presets = {
        "Published medians": LITERATURE,
        "Baseline coefficients": FORMER_DEFAULTS,
        "Section 9 fit": {"diffusivity_mm2_per_day": 0.251, "rho_per_day": 0.106},
    }
    buttons = []
    for name, values in presets.items():
        button = widgets.Button(description=name, layout=widgets.Layout(width="13em"))

        def apply(_, values=values):
            controls["diffusivity_mm2_per_day"].value = values["diffusivity_mm2_per_day"]
            controls["rho_per_day"].value = values["rho_per_day"]

        button.on_click(apply)
        buttons.append(button)
    player, player_box = play_control(
        widgets,
        value=OBSERVED_DAY,
        min=0,
        max=HORIZON_DAYS,
        step=4,
        interval=700,
        description="Play",
    )
    widgets.jslink((player, "value"), (controls["day"], "value"))
    note = widgets.HTML(
        "<small>White-matter guidance is not offered: LUMIERE has no tissue segmentation "
        "(see notebook 02's tissue explorer). The abnormal-tissue factor is a what-if, not a "
        "known property. Plane offset needs the local prepared volumes.</small>"
    )

    def render(plane_offset, day, **settings):
        try:
            current = (
                case
                if plane_offset == 0 or prepared_root is None or base_index is None
                else _plane_case(str(prepared_root), base_index + plane_offset)
            )
            if not current.roi(INITIAL_VISIT, WHOLE_LABELS).any():
                return None, "No week-045 label on this plane; choose another offset."
            problem = check_settings(settings)
            if problem:
                return None, problem
            result = _cached(current, tuple(sorted(settings.items())))
        except ValueError as error:
            return None, f"Not run: {error}"
        figure = plt.figure(figsize=(14, 5.6), constrained_layout=True)
        draw_what_if(figure, current, result, day)
        return figure, (
            f"Plane index {current.metadata.get('slice_index', 'n/a')} "
            f"(offset {plane_offset:+d} mm); "
            f"time step {result['time_step_days']:.3g} day; "
            f"balance residual {result['run'].max_balance_residual_mm2:.1e} mm²."
        )

    groups = widgets.Tab(
        children=[
            widgets.VBox([controls["plane_offset"], controls["boundary_shift_mm"]]),
            widgets.VBox([widgets.HBox([controls["day"], player_box])]),
            widgets.VBox([controls["use_brain_domain"], controls["abnormal_factor"], note]),
            widgets.VBox(
                [
                    widgets.HBox(buttons),
                    *(
                        controls[k]
                        for k in (
                            "diffusivity_mm2_per_day",
                            "rho_per_day",
                            "core_level",
                            "margin_level",
                            "core_threshold",
                            "t2_threshold",
                        )
                    ),
                ]
            ),
        ]
    )
    for i, title in enumerate(("Spatial", "Temporal", "Tissue", "Model")):
        groups.set_title(i, title)
    display(widgets.VBox([groups, figure_widget(render, controls)]))


_RESULTS: dict = {}


def _cached(case: SliceCase, key: tuple) -> dict:
    full_key = (id(case), key)
    if full_key not in _RESULTS:
        if len(_RESULTS) > 24:
            _RESULTS.clear()
        _RESULTS[full_key] = what_if_run(case, **dict(key))
    return _RESULTS[full_key]
