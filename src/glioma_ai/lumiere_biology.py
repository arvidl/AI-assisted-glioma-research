"""Two-level reading of LUMIERE labels, a brain domain and local/distant scoring.

Follows the "tip of the iceberg" convention of Swanson and colleagues: the
contrast-enhancing (T1Gd) boundary is read as about 80% and the T2 boundary as
about 16% of the maximum normalized tumour-cell density (Swanson et al. 2008).
Here the automated core label (1 + 4) stands in for the T1Gd abnormality and the
whole union (1 + 2 + 4) for the T2/FLAIR abnormality. Coefficients are either
prescribed from published patient medians (Wang et al. 2009) or calibrated on
one interval and then reported as a fit. Nothing here registers, segments,
resamples or relabels images; the brain domain is the registered skull-stripped
CT1 support, read explicitly.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from glioma_ai.growth_model import DensityRun, simulate_density_2d
from glioma_ai.lumiere_dynamics import CORE_LABELS, SliceCase, _extent, _format_plane, _save

WHOLE_LABELS = (1, 2, 4)
T1GD_FRACTION = 0.80
T2_FRACTION = 0.16
READING_SOURCE = "Swanson KR et al., Br J Cancer 98:113-119 (2008), doi:10.1038/sj.bjc.6604125"
LITERATURE = {
    "diffusivity_mm2_per_day": 29.7 / 365,
    "rho_per_day": 15 / 365,
    "source": "Wang CH et al., Cancer Res 69:9133-9140 (2009), doi:10.1158/0008-5472.CAN-08-3863",
    "cohort": "32 newly diagnosed glioblastomas, serial pre-treatment MRI",
    "medians": "D 29.7 mm^2/year (range 3.2-468.9), rho 15/year (doubling time 17 days, 1-87)",
    "units_note": "D in mm^2/year as in the article's Methods and Table 2",
}
FORMER_DEFAULTS = {"diffusivity_mm2_per_day": 0.35, "rho_per_day": 0.035}


def front_speed_mm_per_day(diffusivity_mm2_per_day: float, rho_per_day: float) -> float:
    """Asymptotic Fisher--Kolmogorov front speed 2 sqrt(D rho)."""
    return float(2 * np.sqrt(diffusivity_mm2_per_day * rho_per_day))


def front_width_mm(diffusivity_mm2_per_day: float, rho_per_day: float) -> float:
    """Length scale sqrt(D / rho) of the invisible infiltrating margin."""
    return float(np.sqrt(diffusivity_mm2_per_day / rho_per_day))


def _index(case: SliceCase, visit: str) -> int:
    return case.metadata["visit_names"].index(visit)


def brain_domain(case: SliceCase, visit: str = "week-045") -> tuple[np.ndarray, int]:
    """Registered skull-stripped CT1 support at ``visit``, plus that visit's labels.

    Returns the domain and the number of labelled cells outside the CT1 support,
    which are added so that no starting density lies outside the domain.
    """
    brain = case.images[_index(case, visit)] > 0
    labelled = case.roi(visit, WHOLE_LABELS)
    return brain | labelled, int(np.count_nonzero(labelled & ~brain))


def two_level_initial(
    case: SliceCase,
    visit: str = "week-045",
    *,
    core_level: float = 0.9,
    margin_level: float = 0.36,
) -> np.ndarray:
    """Piecewise-constant start: core label at ``core_level``, T2/FLAIR margin at ``margin_level``.

    Both levels are assumptions; they must respect the reading thresholds.
    """
    if not T1GD_FRACTION <= core_level <= 1 or not T2_FRACTION <= margin_level < T1GD_FRACTION:
        raise ValueError("Require 0.80 <= core level <= 1 and 0.16 <= margin level < 0.80.")
    core, whole = case.roi(visit, CORE_LABELS), case.roi(visit, WHOLE_LABELS)
    return np.where(core, core_level, np.where(whole, margin_level, 0.0))


def component_labels(mask: np.ndarray) -> np.ndarray:
    """Integer labels of the 4-connected components of a 2D boolean mask (0 = background)."""
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2:
        raise ValueError("Component labelling requires a 2D mask.")
    labels = np.zeros(mask.shape, dtype=int)
    height, width = mask.shape
    current = 0
    for y0, x0 in np.argwhere(mask):
        if labels[y0, x0]:
            continue
        current += 1
        labels[y0, x0] = current
        stack = [(int(y0), int(x0))]
        while stack:
            y, x = stack.pop()
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not labels[ny, nx]:
                    labels[ny, nx] = current
                    stack.append((ny, nx))
    return labels


def local_and_distant(
    case: SliceCase, initial_visit: str = "week-045", later_visit: str = "week-049"
) -> dict:
    """Split the later labels into in-plane components touching the start and the rest.

    A later whole-union component is *local* if it overlaps the starting whole
    union on this plane, otherwise *distant*. Components may connect through
    other planes; this split sees one plane only.
    """
    start = case.roi(initial_visit, WHOLE_LABELS)
    later_whole, later_core = (
        case.roi(later_visit, WHOLE_LABELS),
        case.roi(later_visit, CORE_LABELS),
    )
    labels = component_labels(later_whole)
    touching = np.unique(labels[start & later_whole])
    local = np.isin(labels, touching[touching > 0])
    return {
        "local_whole": local,
        "local_core": later_core & local,
        "distant_whole": later_whole & ~local,
        "distant_core": later_core & ~local,
        "n_local_components": int((touching > 0).sum()),
        "n_distant_components": int(len(np.unique(labels[later_whole & ~local]))),
    }


def _dice(prediction: np.ndarray, observation: np.ndarray) -> float:
    total = int(prediction.sum() + observation.sum())
    return float(2 * np.count_nonzero(prediction & observation) / total) if total else 1.0


def score_density(
    density: np.ndarray,
    split: dict,
    pixel_area: float,
    *,
    core_threshold: float = T1GD_FRACTION,
    t2_threshold: float = T2_FRACTION,
) -> dict:
    """Two-level reading of a density, scored against local and distant later labels."""
    core, whole = density >= core_threshold, density >= t2_threshold
    return {
        "core_area_mm2": float(core.sum() * pixel_area),
        "whole_area_mm2": float(whole.sum() * pixel_area),
        "local_core_dice": _dice(core, split["local_core"]),
        "local_whole_dice": _dice(whole, split["local_whole"]),
        "local_score": 0.5
        * (_dice(core, split["local_core"]) + _dice(whole, split["local_whole"])),
        "distant_whole_area_mm2": float(split["distant_whole"].sum() * pixel_area),
        "distant_whole_reached_mm2": float((whole & split["distant_whole"]).sum() * pixel_area),
    }


def observed_radial_speeds(
    case: SliceCase, split: dict, initial_visit: str = "week-045", later_visit: str = "week-049"
) -> dict:
    """Change of circle-equivalent radius of the local labels per nominal day (in-plane only)."""
    days = 7 * (int(later_visit.split("-")[1]) - int(initial_visit.split("-")[1]))
    pixel_area = case.dx_mm * case.dy_mm

    def radius(mask: np.ndarray) -> float:
        return float(np.sqrt(mask.sum() * pixel_area / np.pi))

    return {
        "days": days,
        "core_mm_per_day": (
            radius(split["local_core"]) - radius(case.roi(initial_visit, CORE_LABELS))
        )
        / days,
        "whole_mm_per_day": (
            radius(split["local_whole"]) - radius(case.roi(initial_visit, WHOLE_LABELS))
        )
        / days,
    }


def run_two_level(
    case: SliceCase,
    *,
    diffusivity_mm2_per_day: float = LITERATURE["diffusivity_mm2_per_day"],
    rho_per_day: float = LITERATURE["rho_per_day"],
    initial_visit: str = "week-045",
    later_visit: str = "week-049",
    core_level: float = 0.9,
    margin_level: float = 0.36,
    use_brain_domain: bool = True,
    dt_days: float = 0.2,
    n_snapshots: int = 15,
) -> dict:
    """One two-level forward run from ``initial_visit``, scored at ``later_visit``."""
    if initial_visit.startswith("week-000"):
        raise ValueError("This growth-only example must not span the perioperative interval.")
    days = 7 * (int(later_visit.split("-")[1]) - int(initial_visit.split("-")[1]))
    if days <= 0:
        raise ValueError("Choose a strictly later nominal week.")
    initial = two_level_initial(
        case, initial_visit, core_level=core_level, margin_level=margin_level
    )
    domain, added = brain_domain(case, initial_visit) if use_brain_domain else (None, 0)
    run: DensityRun = simulate_density_2d(
        initial,
        diffusivity_mm2_per_day,
        rho_per_day,
        np.linspace(0, days, n_snapshots),
        dx_mm=case.dx_mm,
        dy_mm=case.dy_mm,
        dt_days=dt_days,
        domain=domain,
    )
    split = local_and_distant(case, initial_visit, later_visit)
    pixel_area = case.dx_mm * case.dy_mm
    return {
        "settings": {
            "diffusivity_mm2_per_day": float(diffusivity_mm2_per_day),
            "rho_per_day": float(rho_per_day),
            "days": days,
            "core_level": core_level,
            "margin_level": margin_level,
            "reading_thresholds": (T1GD_FRACTION, T2_FRACTION),
            "brain_domain": use_brain_domain,
            "labelled_cells_added_to_domain": added,
        },
        "front_speed_mm_per_day": front_speed_mm_per_day(diffusivity_mm2_per_day, rho_per_day),
        "front_width_mm": front_width_mm(diffusivity_mm2_per_day, rho_per_day),
        "model": score_density(run.density[-1], split, pixel_area),
        "no_change": score_density(initial, split, pixel_area),
        "split": split,
        "domain": domain,
        "run": run,
        "max_balance_residual_mm2": run.max_balance_residual_mm2,
    }


def compare_variants(case: SliceCase, **kwargs) -> dict:
    """No change, literature medians with and without the brain domain, former defaults."""
    literature = run_two_level(case, **kwargs)
    rectangle = run_two_level(case, use_brain_domain=False, **kwargs)
    former = run_two_level(case, **{**kwargs, **FORMER_DEFAULTS})
    return {
        "No change (two-level reading of week 045)": literature["no_change"],
        "Literature medians, brain domain": literature["model"],
        "Literature medians, whole rectangle": rectangle["model"],
        "Former defaults (D 0.35, rho 0.035), brain domain": former["model"],
    }


def calibration_grid(
    case: SliceCase,
    diffusivities_mm2_per_day: np.ndarray | None = None,
    rhos_per_day: np.ndarray | None = None,
    **kwargs,
) -> dict:
    """Local score over a (D, rho) grid. Choosing a cell from it is a fit to week 049.

    Defaults span roughly the published patient ranges of Wang et al. (2009),
    capped at D = 1 mm^2/day by the explicit stability bound for dt = 0.2 day.
    """
    d_values = (
        np.geomspace(0.01, 1.0, 11)
        if diffusivities_mm2_per_day is None
        else np.asarray(diffusivities_mm2_per_day, dtype=float)
    )
    r_values = np.geomspace(0.008, 0.32, 11) if rhos_per_day is None else np.asarray(rhos_per_day)
    score = np.zeros((len(d_values), len(r_values)))
    core = np.zeros_like(score)
    whole = np.zeros_like(score)
    for i, d in enumerate(d_values):
        for j, r in enumerate(r_values):
            result = run_two_level(
                case, diffusivity_mm2_per_day=d, rho_per_day=r, n_snapshots=2, **kwargs
            )
            score[i, j] = result["model"]["local_score"]
            core[i, j] = result["model"]["local_core_dice"]
            whole[i, j] = result["model"]["local_whole_dice"]
    i, j = np.unravel_index(np.argmax(score), score.shape)
    return {
        "diffusivities_mm2_per_day": d_values,
        "rhos_per_day": r_values,
        "local_score": score,
        "local_core_dice": core,
        "local_whole_dice": whole,
        "best": {
            "diffusivity_mm2_per_day": float(d_values[i]),
            "rho_per_day": float(r_values[j]),
            "local_score": float(score[i, j]),
            "local_core_dice": float(core[i, j]),
            "local_whole_dice": float(whole[i, j]),
            "front_speed_mm_per_day": front_speed_mm_per_day(d_values[i], r_values[j]),
            "front_width_mm": front_width_mm(d_values[i], r_values[j]),
        },
        "near_best_cells": int((score >= score[i, j] - 0.01).sum()),
    }


def identifiability_summary(grid: dict) -> dict:
    """Score range along D at the best rho, and along rho at the best D."""
    score = grid["local_score"]
    i, j = np.unravel_index(np.argmax(score), score.shape)
    return {
        "score_range_along_D": float(np.ptp(score[:, j])),
        "score_range_along_rho": float(np.ptp(score[i, :])),
    }


def write_two_level_figure(case: SliceCase, result: dict, output: Path, name: str) -> Path:
    """Start, model at the later visit, and the local/distant split, on one crop."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    split, run = result["split"], result["run"]
    extent = _extent(case)
    bbox = np.argwhere((run.density[0] > 0) | split["local_whole"] | split["distant_whole"])
    pad = 20
    xlim = (max(bbox[:, 0].min() - pad, 0) * case.dx_mm, (bbox[:, 0].max() + pad) * case.dx_mm)
    ylim = (max(bbox[:, 1].min() - pad, 0) * case.dy_mm, (bbox[:, 1].max() + pad) * case.dy_mm)
    figure, axes = plt.subplots(1, 3, figsize=(14, 5), constrained_layout=True)
    panels = (
        (run.density[0], "Start (week 045): two-level density"),
        (run.density[-1], f"Model after {result['settings']['days']} days"),
    )
    for axis, (density, title) in zip(axes[:2], panels, strict=True):
        image = axis.imshow(density.T, origin="lower", extent=extent, cmap="magma", vmin=0, vmax=1)
        axis.contour(
            density.T >= T1GD_FRACTION,
            levels=[0.5],
            extent=extent,
            colors="#f29b38",
            linewidths=1.4,
        )
        axis.contour(
            density.T >= T2_FRACTION,
            levels=[0.5],
            extent=extent,
            colors="#48dbbf",
            linewidths=1.4,
        )
        axis.set_title(title)
    for mask, color in ((split["local_core"], "#f29b38"), (split["local_whole"], "#48dbbf")):
        if mask.any():
            axes[1].contour(
                mask.T,
                levels=[0.5],
                extent=extent,
                colors=color,
                linewidths=1.0,
                linestyles="dashed",
            )
    if result["domain"] is not None:
        for axis in axes[:2]:
            axis.contour(
                result["domain"].T, levels=[0.5], extent=extent, colors="#bbbbbb", linewidths=0.6
            )
    figure.colorbar(image, ax=list(axes[:2]), shrink=0.8, label="Normalized density proxy c")
    index = case.metadata["visit_names"].index("week-049")
    axes[2].imshow(case.images[index].T, origin="lower", extent=extent, cmap="gray")
    overlay = np.zeros(split["local_whole"].shape)
    overlay[split["local_whole"]] = 1
    overlay[split["distant_whole"]] = 2
    axes[2].imshow(
        np.ma.masked_equal(overlay, 0).T,
        origin="lower",
        extent=extent,
        cmap="cool",
        alpha=0.6,
        vmin=1,
        vmax=2,
    )
    axes[2].set_title("Week 049 labels: local (blue) and distant (pink)")
    for axis in axes:
        axis.set_xlim(*xlim)
        axis.set_ylim(*ylim)
        _format_plane(axis, case)
    handles = [
        Line2D([0], [0], color="#f29b38", lw=2, label="core reading, c ≥ 0.80"),
        Line2D([0], [0], color="#48dbbf", lw=2, label="T2/FLAIR reading, c ≥ 0.16"),
        Line2D([0], [0], color="grey", lw=1.5, ls="--", label="week-049 local labels"),
        Line2D([0], [0], color="#bbbbbb", lw=1, label="brain domain"),
    ]
    figure.legend(handles=handles, loc="outside lower center", ncols=4)
    _save(figure, output, name)
    return output / f"{name}.png"


def write_identifiability_figure(
    grid: dict, output: Path, observed_speed_mm_per_day: float, name: str = "lumiere_fit"
) -> Path:
    """Local score over (D, rho), with lines of equal front speed and equal margin width."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    d, r = grid["diffusivities_mm2_per_day"], grid["rhos_per_day"]
    figure, axis = plt.subplots(figsize=(7.5, 6), constrained_layout=True)
    mesh = axis.pcolormesh(r, d, grid["local_score"], shading="nearest", cmap="viridis")
    figure.colorbar(mesh, ax=axis, label="Local score: mean of core and T2/FLAIR Dice")
    rr, dd = np.meshgrid(np.geomspace(r[0], r[-1], 200), np.geomspace(d[0], d[-1], 200))
    speed = axis.contour(
        rr,
        dd,
        2 * np.sqrt(dd * rr),
        levels=[observed_speed_mm_per_day],
        colors="white",
        linestyles="dashed",
    )
    axis.clabel(speed, fmt=lambda v: f"2√(Dρ) = {v:.2f} mm/day")
    width = axis.contour(
        rr, dd, np.sqrt(dd / rr), levels=[0.5, 1, 2, 4], colors="#ffd166", linewidths=0.8
    )
    axis.clabel(width, fmt=lambda v: f"√(D/ρ) = {v:g} mm")
    axis.plot(
        LITERATURE["rho_per_day"],
        LITERATURE["diffusivity_mm2_per_day"],
        "o",
        color="#ef476f",
        label="Published median (Wang et al. 2009)",
    )
    best = grid["best"]
    axis.plot(
        best["rho_per_day"],
        best["diffusivity_mm2_per_day"],
        "*",
        ms=14,
        color="white",
        label="Best grid cell (a fit to week 049)",
    )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Net proliferation ρ (1/day)")
    axis.set_ylabel("Net migration D (mm²/day)")
    axis.legend(loc="lower left", fontsize=8)
    axis.set_title("What one interval can identify")
    _save(figure, output, name)
    return output / f"{name}.png"
