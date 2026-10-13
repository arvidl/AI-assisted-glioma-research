"""Mathematical and visual controls for the day-scale 2D density experiment."""

import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

from glioma_ai.growth_model import simulate_density_2d, solver_controls
from glioma_ai.provenance import environment_record, sha256


def density_animation(density, days, extent, *, title: str) -> str:
    """Return a notebook time slider/playback with a fixed 0--1 color scale."""
    figure, axis = plt.subplots(figsize=(5, 4.5), constrained_layout=True)
    image = axis.imshow(density[0].T, origin="lower", extent=extent, cmap="magma", vmin=0, vmax=1)
    heading = axis.set_title(f"{title}\nt = {days[0]:g} days")
    axis.set_xlabel("Image-plane axis 0 (mm)")
    axis.set_ylabel("Image-plane axis 1 (mm)")
    figure.colorbar(image, ax=axis, label="Normalized density proxy c")

    def update(index):
        image.set_data(density[index].T)
        heading.set_text(f"{title}\nt = {days[index]:g} days")
        return image, heading

    animation = FuncAnimation(figure, update, frames=len(days), interval=350, blit=False)
    html = animation.to_jshtml()
    plt.close(figure)
    return html


def controls_animation(densities: dict, days, coordinates, *, half_width_mm: float = 22) -> str:
    """Play several runs side by side on one fixed 0--1 scale, with M in each title."""
    names = list(densities)
    area = float(coordinates[1] - coordinates[0]) ** 2
    h = float(coordinates[1] - coordinates[0]) / 2
    extent = (coordinates[0] - h, coordinates[-1] + h, coordinates[0] - h, coordinates[-1] + h)
    figure, axes = plt.subplots(
        1, len(names), figsize=(3.1 * len(names) + 1, 3.9), constrained_layout=True
    )
    images, headings, contours = [], [], [[] for _ in names]

    def heading(name, index):
        mass = densities[name][index].sum() * area
        return f"{name}\nM = {mass:.1f} mm²"

    for axis, name in zip(axes, names, strict=True):
        images.append(
            axis.imshow(
                densities[name][0].T, origin="lower", extent=extent, cmap="magma", vmin=0, vmax=1
            )
        )
        headings.append(axis.set_title(heading(name, 0), fontsize=10))
        axis.set_xlim(-half_width_mm, half_width_mm)
        axis.set_ylim(-half_width_mm, half_width_mm)
        axis.set_xlabel("Synthetic x (mm)")
    axes[0].set_ylabel("Synthetic y (mm)")
    figure.colorbar(images[-1], ax=list(axes), shrink=0.85, label="Normalized density proxy c")
    clock = figure.suptitle(f"Five controls, same seed and colour scale; t = {days[0]:g} days")

    def draw_contours(index):
        for k, (axis, name) in enumerate(zip(axes, names, strict=True)):
            for artist in contours[k]:
                artist.remove()
            field = densities[name][index].T
            levels = [v for v in (0.1, 0.5) if field.min() < v < field.max()]
            colours = ["#84dfdb" if v == 0.1 else "white" for v in levels]
            contours[k] = (
                [axis.contour(coordinates, coordinates, field, levels, colors=colours)]
                if levels
                else []
            )

    def update(index):
        for image, title, name in zip(images, headings, names, strict=True):
            image.set_data(densities[name][index].T)
            title.set_text(heading(name, index))
        draw_contours(index)
        clock.set_text(f"Five controls, same seed and colour scale; t = {days[index]:g} days")
        return images

    draw_contours(0)
    animation = FuncAnimation(figure, update, frames=len(days), interval=450, blit=False)
    html = animation.to_jshtml()
    plt.close(figure)
    return html


def write_growth_experiment(output: Path, paper_dir: Path | None = None) -> dict:
    """Save time-resolved synthetic controls with no external inputs or AI calls."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    coordinates = np.arange(81, dtype=float) - 40
    x, y = np.meshgrid(coordinates, coordinates, indexing="ij")
    initial = 0.65 * (x * x + y * y <= 7**2)
    days = np.arange(0, 29, 2, dtype=float)
    d, rho, dt = 0.35, 0.035, 0.2
    variants = {
        "No change": (0.0, 0.0),
        "Diffusion only": (d, 0.0),
        "Reaction only": (0.0, rho),
        "Reaction + diffusion": (d, rho),
        "Double D": (2 * d, rho),
    }
    runs = {
        name: simulate_density_2d(initial, diffusion, reaction, days, dt_days=dt)
        for name, (diffusion, reaction) in variants.items()
    }
    model = runs["Reaction + diffusion"]
    figure, axes = plt.subplots(2, 3, figsize=(12.5, 8), constrained_layout=True)
    for axis, i, letter in zip(axes[0], (0, 7, 14), "ABC", strict=True):
        panel = axis.imshow(
            model.density[i].T,
            origin="lower",
            extent=(-40.5, 40.5, -40.5, 40.5),
            cmap="magma",
            vmin=0,
            vmax=1,
        )
        axis.contour(
            coordinates,
            coordinates,
            model.density[i].T,
            levels=[0.1, 0.5],
            colors=["#84dfdb", "white"],
        )
        axis.set_xlim(-22, 22)
        axis.set_ylim(-22, 22)
        axis.set_xlabel("Synthetic x (mm)")
        axis.set_ylabel("Synthetic y (mm)")
        axis.set_title(f"{letter}  Reaction + diffusion, t = {days[i]:g} days", loc="left")
    axes[0, 0].legend(
        handles=[
            Line2D([], [], color="#84dfdb", lw=1.5, label="contour c = 0.1"),
            Line2D([], [], color="white", lw=1.5, label="contour c = 0.5"),
        ],
        loc="lower left",
        fontsize=8,
        facecolor="#333333",
        labelcolor="white",
    )
    figure.colorbar(panel, ax=list(axes[0]), label="Normalized density proxy c", shrink=0.8)
    styles = {
        "No change": {"color": "black", "ls": ":", "lw": 2, "zorder": 3},
        "Diffusion only": {"color": "#1f77b4"},
        "Reaction only": {"color": "#ff7f0e"},
        "Reaction + diffusion": {"color": "#2ca02c"},
        "Double D": {"color": "#d62728"},
    }
    for name, run in runs.items():
        style = styles[name]
        axes[1, 0].plot(days, run.integral_mm2, label=name, **style)
        axes[1, 1].plot(days, run.areas_mm2(0.5), label=name, **style)
    axes[1, 0].set_ylabel("M = ∫c dA (mm²); not a cell count")
    axes[1, 1].set_ylabel("Area at c ≥ 0.5 (mm²)")
    axes[1, 0].set_title("D  Integrated density proxy, five controls", loc="left")
    axes[1, 1].set_title("E  Thresholded area, five controls", loc="left")
    for axis in axes[1, :2]:
        axis.set_xlabel("Elapsed model time (days)")
        axis.legend(fontsize=8)
    for level in (0.1, 0.3, 0.5):
        axes[1, 2].plot(days, model.areas_mm2(level), label=f"Threshold {level:g}")
    axes[1, 2].set_xlabel("Elapsed model time (days)")
    axes[1, 2].set_ylabel("Area at an uncalibrated threshold (mm²)")
    axes[1, 2].set_title("F  One solution, three display thresholds", loc="left")
    axes[1, 2].legend(fontsize=8)
    figure.suptitle(
        "Synthetic proliferation–invasion experiment: transport, reaction and observation\n"
        "Prescribed c₀ = 0.65 inside a 7-mm disk; D = 0.35 mm²/day; ρ = 0.035/day"
    )
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"growth_controls.{suffix}", dpi=170, bbox_inches="tight")
    plt.close(figure)
    checks = solver_controls()
    refined = simulate_density_2d(initial, d, rho, days, dt_days=dt / 2)
    binary_reaction = simulate_density_2d((initial > 0).astype(float), 0, rho, [0, 28])
    result = {
        "evidence_type": "synthetic",
        "state": "unmeasured normalized density proxy",
        "equation": "dc/dt = div(D grad c) + rho c (1-c)",
        "parameters": {
            "D_mm2_per_day": d,
            "rho_per_day": rho,
            "initial_occupancy": 0.65,
            "radius_mm": 7,
            "dx_mm": 1,
            "dy_mm": 1,
            "elapsed_days": 28,
            "dt_days_max": dt,
        },
        "solver": "exact half reaction / conservative Euler diffusion / exact half reaction",
        "boundary": "no flux at outer rectangle",
        "controls": {
            name: {
                "initial_integral_mm2": float(run.integral_mm2[0]),
                "final_integral_mm2": float(run.integral_mm2[-1]),
                "final_area_threshold_05_mm2": float(run.areas_mm2(0.5)[-1]),
                "max_balance_residual_mm2": run.max_balance_residual_mm2,
            }
            for name, run in runs.items()
        },
        "analytic_verification": checks,
        "step_halving_density_rms": float(
            np.sqrt(np.mean((model.density[-1] - refined.density[-1]) ** 2))
        ),
        "binary_initialization_reaction_only_change": float(
            np.max(np.abs(binary_reaction.density[-1] - binary_reaction.density[0]))
        ),
        "patient_coefficients_fitted": False,
        "clinical_validation": "not_performed",
        "ai_contribution": (
            "research assistance with implementation/explanation; solver is classical"
        ),
    }
    (output / "growth_controls.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    np.savez_compressed(
        output / "growth_snapshots.npz",
        days=days,
        density=model.density,
        control_names=np.array(list(runs)),
        control_density=np.stack([run.density for run in runs.values()]),
        initial=initial,
        x_mm=coordinates,
        y_mm=coordinates,
    )
    artifacts = [
        output / name
        for name in (
            "growth_controls.png",
            "growth_controls.pdf",
            "growth_controls.json",
            "growth_snapshots.npz",
        )
    ]
    (output / "growth_run.json").write_text(
        json.dumps(
            {
                **environment_record(),
                "inputs": "synthetic disk; no external data",
                "parameters": result["parameters"],
                "output_sha256": {p.name: sha256(p) for p in artifacts},
            },
            indent=2,
        )
        + "\n"
    )
    if paper_dir is not None:
        Path(paper_dir).mkdir(parents=True, exist_ok=True)
        shutil.copy2(output / "growth_controls.pdf", Path(paper_dir) / "growth_controls.pdf")
    return result


def write_tissue_experiment(output: Path) -> dict:
    """Figure 2: tissue-guided anisotropic spread on a constructed coronal phantom."""
    from glioma_ai.growth_interactive import (
        SCENARIO_COLOURS,
        TISSUE_DAYS,
        draw_density_on_tissue,
        draw_tissue_map,
        tissue_legend_handles,
    )
    from glioma_ai.tissue_growth import (
        FIBRE_NAMES,
        TISSUE_NAMES,
        contralateral_summary,
        coronal_phantom,
        tissue_scenarios,
        tissue_solver_controls,
        tumour_seed,
    )

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    phantom = coronal_phantom()
    seed = tumour_seed(phantom)
    parameters = {
        "grey_mm2_per_day": 0.1,
        "white_to_grey": 5.0,
        "fibre_ratio": 2.0,
        "rho_per_day": 0.035,
    }
    runs = tissue_scenarios(phantom, **parameters, days=TISSUE_DAYS, seed=seed)
    names = list(runs)
    guided = runs[names[-1]][0]
    shown = (120, 240, 365)
    figure, axes = plt.subplots(2, 3, figsize=(15, 9.5), constrained_layout=True)
    draw_tissue_map(axes[0, 0], phantom)
    axes[0, 0].contour(phantom.x_mm, phantom.y_mm, seed.T, [0.3], colors="#d62728")
    axes[0, 0].legend(
        handles=tissue_legend_handles()
        + [Line2D([], [], color="#d62728", label="seed, c₀ = 0.65 (left parietal)")],
        loc="lower center",
        fontsize=7,
        ncol=2,
    )
    axes[0, 0].set_title("A  Constructed tissue and fibre directions", loc="left")
    for axis, day, letter in zip((axes[0, 1], axes[0, 2], axes[1, 0]), shown, "BCD", strict=True):
        image = draw_density_on_tissue(axis, phantom, guided.density[list(guided.days).index(day)])
        axis.set_title(f"{letter}  Tissue-guided, t = {day} days", loc="left")
    axes[0, 1].legend(
        handles=[
            Line2D([], [], color="#00a0c8", label="contour c = 0.1"),
            Line2D([], [], color="black", label="contour c = 0.5"),
        ],
        loc="lower center",
        fontsize=8,
    )
    for axis in (axes[0, 2], axes[1, 0]):
        figure.colorbar(image, ax=axis, shrink=0.75, label="Normalized density proxy c")
    compare = list(guided.days).index(240)
    draw_tissue_map(axes[1, 1], phantom, glyph_every_mm=1e9)
    for name, colour in zip(names, SCENARIO_COLOURS, strict=True):
        field = runs[name][0].density[compare].T
        axes[1, 1].contour(phantom.x_mm, phantom.y_mm, field, [0.1], colors=colour, linewidths=1.5)
    axes[1, 1].legend(
        handles=[
            Line2D([], [], color=c, label=n) for n, c in zip(names, SCENARIO_COLOURS, strict=True)
        ],
        loc="lower center",
        fontsize=7,
    )
    axes[1, 1].set_title("E  Contour c = 0.1 at 240 days, three assumptions", loc="left")
    summaries = {}
    for name, colour in zip(names, SCENARIO_COLOURS, strict=True):
        summary = contralateral_summary(phantom, runs[name][0])
        summaries[name] = summary
        axes[1, 2].plot(
            guided.days, 100 * summary["contralateral_fraction"], color=colour, label=name
        )
        if summary["first_day_at_threshold"] is not None:
            axes[1, 2].axvline(summary["first_day_at_threshold"], color=colour, ls=":", lw=1)
    axes[1, 2].set_xlabel("Elapsed model time (days)")
    axes[1, 2].set_ylabel("Share of M in patient-right hemisphere (%)")
    axes[1, 2].set_title("F  Contralateral share of M", loc="left")
    axes[1, 2].text(
        0.02,
        0.6,
        "dotted: first day with\nc ≥ 0.1 across the midline",
        transform=axes[1, 2].transAxes,
        fontsize=8,
    )
    axes[1, 2].legend(fontsize=8)
    figure.suptitle(
        "Synthetic tissue-guided proliferation–invasion on a constructed coronal phantom "
        "(radiological view: patient left on the right)\n"
        "D_g = 0.1 mm²/day; white matter 5 × D_g; along labelled fibres 2 × D_w; "
        "ρ = 0.035/day in brain tissue; CSF and outside are no-flux barriers"
    )
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"tissue_growth.{suffix}", dpi=150, bbox_inches="tight")
    plt.close(figure)
    result = {
        "evidence_type": "synthetic",
        "state": "unmeasured normalized density proxy",
        "equation": "dc/dt = d/dx(D_xx dc/dx) + d/dy(D_yy dc/dy) + rho(x,y) c (1-c)",
        "phantom": {
            "kind": "constructed coronal slice; not an atlas, image or segmentation",
            "shape": list(phantom.tissue.shape),
            "spacing_mm": phantom.spacing_mm,
            "x_axis": "patient right (negative) to patient left (positive)",
            "y_axis": "inferior (negative) to superior (positive)",
            "tissue_cells": {
                TISSUE_NAMES[k]: int((phantom.tissue == k).sum()) for k in TISSUE_NAMES
            },
            "fibre_cells": {FIBRE_NAMES[k]: int((phantom.fibre == k).sum()) for k in FIBRE_NAMES},
        },
        "seed": {"centre_mm": [38.0, 27.0], "radius_mm": 5.0, "occupancy": 0.65},
        "parameters": parameters,
        "scenarios": {
            name: {
                "dt_days": runs[name][0].largest_step_days,
                "positivity_limit_days": runs[name][0].step_limit_days,
                "n_steps": runs[name][0].n_steps,
                "final_integral_mm2": float(runs[name][0].integral_mm2[-1]),
                "contralateral_share_day_240": float(
                    summaries[name]["contralateral_fraction"][compare]
                ),
                "contralateral_share_day_365": float(summaries[name]["contralateral_fraction"][-1]),
                "first_day_c_ge_0.1_across_midline": summaries[name]["first_day_at_threshold"],
                "max_balance_residual_mm2": runs[name][0].max_balance_residual_mm2,
            }
            for name in names
        },
        "verification": tissue_solver_controls(),
        "patient_coefficients_fitted": False,
        "clinical_validation": "not_performed",
        "ai_contribution": (
            "research assistance with implementation/explanation; solver is classical"
        ),
    }
    (output / "tissue_growth.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    artifacts = [output / f"tissue_growth.{s}" for s in ("png", "pdf", "json")]
    (output / "tissue_growth_run.json").write_text(
        json.dumps(
            {
                **environment_record(),
                "inputs": "constructed phantom and seed; no external data",
                "parameters": parameters,
                "output_sha256": {p.name: sha256(p) for p in artifacts},
            },
            indent=2,
        )
        + "\n"
    )
    return result
