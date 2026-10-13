"""Figures, records and an explorer for the constructed network notebook.

Drawing functions take precomputed runs and work with any Matplotlib backend;
the explorer imports ipywidgets lazily (notebooks dependency group).
"""

import json
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from glioma_ai.growth_interactive import (
    SCENARIO_COLOURS,
    TISSUE_DAYS,
    _cached_tissue,
    _with_player,
    draw_density_on_tissue,
)
from glioma_ai.network import (
    COGNITIVE_ASSUMPTIONS,
    PhantomNetwork,
    lesion_course,
    linear_controls,
    linear_fc,
    phantom_network,
    resection_state,
    spectral_radius,
    tract_integrity,
)
from glioma_ai.tissue_growth import CoronalPhantom

DEFAULT_GROWTH = (0.1, 5.0, 2.0, 0.035)


def draw_tracts(axis, phantom: CoronalPhantom, network: PhantomNetwork, integrity, *, cavity=None):
    """Tract proxies coloured by assumed integrity, width by healthy weight, nodes at centroids."""
    cmap = plt.get_cmap("RdYlGn")
    order = np.argsort(np.triu(network.weight, 1).ravel())
    for flat in order:
        i, j = divmod(int(flat), network.size)
        if j <= i:
            continue
        path = network.paths[i][j]
        axis.plot(
            phantom.x_mm[path[:, 0]],
            phantom.y_mm[path[:, 1]],
            color=cmap(float(integrity[i, j])),
            lw=0.4 + 2.2 * network.weight[i, j],
            alpha=0.35 + 0.6 * network.weight[i, j],
        )
    if cavity is not None and cavity.any():
        axis.contourf(
            phantom.x_mm,
            phantom.y_mm,
            cavity.T.astype(float),
            [0.5, 1.5],
            colors="black",
            alpha=0.55,
        )
    axis.scatter(*network.centroid_mm.T, s=26, color="#1b1b1b", zorder=5)
    for k, name in enumerate(network.names):
        x, y = network.centroid_mm[k]
        axis.annotate(
            name.split("-")[1], (x, y), fontsize=6, xytext=(3, 3), textcoords="offset points"
        )


def _matrix(axis, figure, values, names, title, *, cmap, vmin, vmax, label):
    image = axis.imshow(values, cmap=cmap, vmin=vmin, vmax=vmax)
    axis.set_xticks(range(len(names)), names, rotation=90, fontsize=6)
    axis.set_yticks(range(len(names)), names, fontsize=6)
    half = len(names) / 2 - 0.5
    axis.axhline(half, color="black", lw=0.6)
    axis.axvline(half, color="black", lw=0.6)
    axis.set_title(title, loc="left", fontsize=10)
    figure.colorbar(image, ax=axis, shrink=0.75, label=label)


def draw_network_state(figure, phantom, network, runs: dict, day: float, *, coupling=0.8):
    """Tracts on the tissue-guided state, healthy weights, FC change and courses over time."""
    names = list(runs)
    guided = runs[names[-1]][0]
    index = int(np.argmin(np.abs(guided.days - day)))
    density = guided.density[index]
    integrity = tract_integrity(network, density)
    scale = spectral_radius(network.weight)
    _, fc0 = linear_fc(network.weight / scale, coupling)
    _, fc = linear_fc(network.weight * integrity / scale, coupling)
    axes = figure.subplots(1, 4, gridspec_kw={"width_ratios": [1.25, 1, 1, 1.05]})
    draw_density_on_tissue(axes[0], phantom, density, alpha=0.4)
    draw_tracts(axes[0], phantom, network, integrity)
    axes[0].set_title(
        f"A  Tract proxies, tissue-guided run, day {guided.days[index]:g}", loc="left", fontsize=10
    )
    short = [n.replace("-", " ") for n in network.names]
    _matrix(
        axes[1],
        figure,
        network.weight,
        short,
        "B  Healthy weights exp(−L/λ)",
        cmap="viridis",
        vmin=0,
        vmax=1,
        label="Weight (dimensionless)",
    )
    _matrix(
        axes[2],
        figure,
        fc - fc0,
        short,
        "C  Change in model FC",
        cmap="RdBu_r",
        vmin=-0.3,
        vmax=0.3,
        label="Δ correlation (lesion − healthy)",
    )
    for name, colour in zip(names, SCENARIO_COLOURS, strict=True):
        course = lesion_course(phantom, network, runs[name][0], coupling=coupling)
        axes[3].plot(course["days"], 100 * course["inter_sc"], color=colour, label=name)
    spared = lesion_course(phantom, network, guided, coupling=coupling, spare_callosum=True)
    axes[3].plot(
        spared["days"],
        100 * spared["inter_sc"],
        color=SCENARIO_COLOURS[-1],
        ls="--",
        label="Tissue-guided, callosum assumed uninvolved",
    )
    axes[3].axvline(guided.days[index], color="black", lw=0.8, ls=":")
    axes[3].set_ylim(0, 105)
    axes[3].set_xlabel("Elapsed model time (days)")
    axes[3].set_ylabel("Interhemispheric weight (% of healthy)")
    axes[3].set_title("D  Interhemispheric structural weight", loc="left", fontsize=10)
    axes[3].legend(fontsize=6.5, loc="lower left")


def draw_resection(figure, phantom, network, state: dict, day: float) -> None:
    """Cavity and cut tracts, node strength, FC change after resection, assumed domains."""
    axes = figure.subplots(1, 4, gridspec_kw={"width_ratios": [1.25, 1.1, 1, 1.1]})
    weights = state["weights"]
    integrity = np.divide(
        weights["post-operative"],
        network.weight,
        out=np.ones_like(network.weight),
        where=network.weight > 0,
    )
    draw_density_on_tissue(axes[0], phantom, np.zeros_like(phantom.tissue, dtype=float))
    draw_tracts(axes[0], phantom, network, integrity, cavity=state["cavity"])
    axes[0].set_title(
        f"A  Cavity (c ≥ {state['threshold']:g}, day {day:g}) and tracts", loc="left", fontsize=10
    )
    position = np.arange(network.size)
    for k, (name, colour) in enumerate(
        zip(weights, ("#4d4d4d", "#e08214", "#542788"), strict=True)
    ):
        axes[1].bar(
            position + (k - 1) * 0.28,
            weights[name].sum(axis=1),
            width=0.28,
            color=colour,
            label=name,
        )
    axes[1].set_xticks(position, network.names, rotation=90, fontsize=6)
    axes[1].set_ylabel("Node strength Σ_j w_ij (dimensionless)")
    axes[1].set_title("B  Node strength", loc="left", fontsize=10)
    axes[1].legend(fontsize=7)
    short = [n.replace("-", " ") for n in network.names]
    change = state["fc"]["post-operative"] - state["fc"]["pre-operative"]
    span = max(0.02, float(np.abs(change).max()))
    _matrix(
        axes[2],
        figure,
        change,
        short,
        "C  Model FC, post − pre",
        cmap="RdBu_r",
        vmin=-span,
        vmax=span,
        label="Δ correlation",
    )
    domains = [d for d, keys in COGNITIVE_ASSUMPTIONS.items() if keys]
    y = np.arange(len(domains))
    for k, (name, colour) in enumerate(
        (("pre-operative", "#e08214"), ("post-operative", "#542788"))
    ):
        values = [100 * state["domains"][name][d]["L"] for d in domains]
        axes[3].barh(y + (k - 0.5) * 0.36, values, height=0.36, color=colour, label=f"{name}, left")
    axes[3].axvline(100, color="black", lw=0.8)
    axes[3].set_yticks(y, domains, fontsize=7)
    axes[3].set_xlabel("Left-hemisphere node strength (% of healthy)")
    axes[3].set_title("D  Assumed CANTAB regions (unsourced)", loc="left", fontsize=10)
    axes[3].legend(fontsize=6.5, loc="lower left")
    axes[3].text(
        0.02,
        -0.32,
        "SOC planning: frontal, not in this slice",
        transform=axes[3].transAxes,
        fontsize=7,
    )


def network_legend() -> list:
    cmap = plt.get_cmap("RdYlGn")
    return [
        Line2D([], [], color=cmap(1.0), lw=2, label="tract intact (integrity 1)"),
        Line2D([], [], color=cmap(0.5), lw=2, label="integrity 0.5"),
        Line2D([], [], color=cmap(0.0), lw=2, label="tract cut (integrity 0)"),
    ]


def write_network_experiment(
    output: Path, *, day: float = 180.0, surgery_day: float = 120.0, coupling: float = 0.8
) -> dict:
    """Figures and records for notebook 11 from the default Figure 2 growth runs."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    phantom, runs, _ = _cached_tissue(*DEFAULT_GROWTH)
    network = phantom_network(phantom)
    guided = runs[list(runs)[-1]][0]
    index = int(np.argmin(np.abs(guided.days - day)))
    figure = plt.figure(figsize=(19, 4.9), constrained_layout=True)
    draw_network_state(figure, phantom, network, runs, day, coupling=coupling)
    figure.legend(handles=network_legend(), loc="lower left", fontsize=7, ncols=3)
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"network_lesion.{suffix}", dpi=160)
    plt.close(figure)
    surgery = int(np.argmin(np.abs(guided.days - surgery_day)))
    state = resection_state(phantom, network, guided.density[surgery], coupling=coupling)
    figure = plt.figure(figsize=(19, 4.9), constrained_layout=True)
    draw_resection(figure, phantom, network, state, guided.days[surgery])
    figure.legend(handles=network_legend(), loc="lower left", fontsize=7, ncols=3)
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"network_resection.{suffix}", dpi=160)
    plt.close(figure)
    courses = {
        name: lesion_course(phantom, network, run, coupling=coupling)
        for name, (run, _) in runs.items()
    }
    courses["Tissue-guided, callosum assumed uninvolved"] = lesion_course(
        phantom, network, guided, coupling=coupling, spare_callosum=True
    )
    at = {
        name: {
            "interhemispheric_weight_percent": round(100 * float(c["inter_sc"][index]), 1),
            "global_efficiency_percent": round(100 * float(c["efficiency"][index]), 1),
            "mean_interhemispheric_fc": round(float(c["inter_fc"][index]), 3),
        }
        for name, c in courses.items()
    }
    record = {
        "evidence_type": "synthetic_construction",
        "network": {
            "nodes": list(network.names),
            "decay_length_mm": network.decay_mm,
            "edge_rule": "shortest 8-connected white-matter path; weight exp(-L/decay)",
            "damage_rule": "integrity = exp(-sum(c) ds / 10 mm) along path; "
            "0 if the path crosses the cavity",
        },
        "dynamics": {
            "model": "dx/dt = -x + g W x + sigma xi; W divided by healthy spectral radius",
            "coupling_g": coupling,
            "time_unit": "node time constant tau",
            "fc": "exact stationary correlation (sigma^2/2)(I - gW)^-1, normalised",
        },
        "day": float(guided.days[index]),
        "healthy_mean_interhemispheric_fc": round(courses[list(runs)[0]]["healthy_inter_fc"], 3),
        "scenarios_at_day": at,
        "resection": {
            "day": float(guided.days[surgery]),
            "threshold": state["threshold"],
            "cavity_area_mm2": state["cavity_area_mm2"],
            "rule": "left-hemisphere white matter at c >= threshold; "
            "corpus callosum and grey matter spared",
            "interhemispheric_weight_percent": {
                name: round(
                    100
                    * s["interhemispheric_weight"]
                    / state["summaries"]["healthy"]["interhemispheric_weight"],
                    1,
                )
                for name, s in state["summaries"].items()
            },
            "assumed_domain_left_strength_percent": {
                name: {
                    d: (None if v is None else round(100 * v["L"], 1)) for d, v in domains.items()
                }
                for name, domains in state["domains"].items()
            },
        },
        "controls": linear_controls(network.weight / spectral_radius(network.weight), coupling),
        "cognitive_mapping": "assumed and unsourced; comparison template, not a prediction",
    }
    (output / "network_experiment.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


@lru_cache(maxsize=2)
def _cached_network():
    phantom, _, _ = _cached_tissue(*DEFAULT_GROWTH)
    return phantom_network(phantom)


def network_explorer():
    """Day, resection threshold and coupling for the default tissue-guided run."""
    import ipywidgets as widgets
    from IPython.display import display

    style = {"description_width": "15em"}
    layout = widgets.Layout(width="38em")
    controls = {
        "day": widgets.IntSlider(
            240, min=0, max=int(TISSUE_DAYS[-1]), step=5, description="Observation / surgery day"
        ),
        "resect": widgets.Checkbox(False, description="Show resection"),
        "threshold": widgets.FloatSlider(
            0.3, min=0.1, max=0.9, step=0.05, description="Cavity threshold c ≥"
        ),
        "coupling": widgets.FloatSlider(
            0.8, min=0.0, max=0.95, step=0.05, description="Coupling g"
        ),
    }
    for control in controls.values():
        control.style, control.layout, control.continuous_update = style, layout, False

    def show(day, resect, threshold, coupling):
        phantom, runs, _ = _cached_tissue(*DEFAULT_GROWTH)
        network = _cached_network()
        figure = plt.figure(figsize=(19, 4.9), constrained_layout=True)
        if resect:
            guided = runs[list(runs)[-1]][0]
            index = int(np.argmin(np.abs(guided.days - day)))
            state = resection_state(
                phantom, network, guided.density[index], threshold=threshold, coupling=coupling
            )
            draw_resection(figure, phantom, network, state, guided.days[index])
        else:
            draw_network_state(figure, phantom, network, runs, day, coupling=coupling)
        plt.show()

    display(_with_player(widgets, controls, show, interval_ms=900))
