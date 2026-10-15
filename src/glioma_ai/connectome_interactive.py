"""Resection size and location on one patient's pre-operative connectome (notebook 12).

A sphere of radius r (mm) is removed around a chosen centre in sub-PAT16's
pre-operative native T1w space (scanner RAS, mm). The tractogram stays outside
Git, so the 82-region matrices cannot say which streamlines cross an arbitrary
sphere. Two stated geometric proxies replace that:
- a region whose centroid lies inside the sphere loses every connection;
- a connection whose straight centroid-to-centroid segment passes through the
  sphere is cut.
Real bundles curve and fan out, and they do not run between centroids, so this
is a teaching device, not a tractography result. The table from CANTAB measures
to regions is an assumption; the explorer imports ipywidgets lazily.
"""

from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import ArrayLike, NDArray

from glioma_ai.connectome import CaseConnectome, load_case, model_weights, upper
from glioma_ai.connectome_figures import _matrix, display_order
from glioma_ai.network import global_efficiency, linear_fc, spectral_radius

TUMOUR_CENTRE = "Tumour-weighted centre"

# Assumed, unsourced mapping from CANTAB measures to Desikan-Killiany regions
# (both hemispheres), for illustrating a comparison template only. The sets
# overlap, and the tasks also depend on regions and tracts not listed here.
ASSUMED_DOMAINS = {
    "SOC planning": (
        "rostralmiddlefrontal",
        "caudalmiddlefrontal",
        "superiorfrontal",
        "parsopercularis",
        "Caudate",
    ),
    "SSP spatial span": (
        "superiorparietal",
        "inferiorparietal",
        "supramarginal",
        "precuneus",
        "caudalmiddlefrontal",
    ),
    "RVP sustained attention": (
        "rostralmiddlefrontal",
        "inferiorparietal",
        "supramarginal",
        "caudalanteriorcingulate",
        "insula",
    ),
    "RTI reaction time": ("precentral", "paracentral", "superiorfrontal", "Thalamus", "Putamen"),
    "MOT motor latency": ("precentral", "postcentral", "paracentral", "Thalamus", "Putamen"),
}


def segment_distance(start: ArrayLike, end: ArrayLike, centre: ArrayLike) -> NDArray:
    """Shortest distance (mm) from a point to each straight segment start[k]-end[k]."""
    a, b, c = (np.asarray(v, dtype=float) for v in (start, end, centre))
    d = b - a
    length2 = np.einsum("...i,...i", d, d)
    t = np.einsum("...i,...i", c - a, d) / np.where(length2 > 0, length2, 1.0)
    nearest = a + np.clip(t, 0.0, 1.0)[..., None] * d
    return np.linalg.norm(nearest - c, axis=-1)


def tumour_weighted_centre(case: CaseConnectome) -> NDArray[np.float64]:
    """Mean of region centroids weighted by each region's share inside the tumour mask (mm)."""
    w = case.tumour_fraction
    return (w[:, None] * case.centroid_mm).sum(axis=0) / w.sum()


def centre_of(case: CaseConnectome, location: str) -> NDArray[np.float64]:
    if location == TUMOUR_CENTRE:
        return tumour_weighted_centre(case)
    return case.centroid_mm[case.names.index(location)]


def sphere_resection(
    case: CaseConnectome, centre_mm: ArrayLike, radius_mm: float, *, cut_tracts: bool = True
) -> dict:
    """Pre-operative weights after removing a sphere, by the two proxies of this module.

    A region is removed when its centroid is strictly inside the sphere; with
    cut_tracts, a pair is also cut when its centroid-to-centroid segment passes
    strictly inside. Radius 0 therefore changes nothing.
    """
    xyz, centre, radius = case.centroid_mm, np.asarray(centre_mm, dtype=float), float(radius_mm)
    removed = np.linalg.norm(xyz - centre, axis=1) < radius
    cut = removed[:, None] | removed[None, :]
    if cut_tracts:
        cut |= segment_distance(xyz[:, None, :], xyz[None, :, :], centre) < radius
    np.fill_diagonal(cut, False)
    return {"removed": removed, "cut": cut, "sc": np.where(cut, 0.0, case.sc["preop"])}


def domain_strength(case: CaseConnectome, strength_ratio: ArrayLike) -> dict:
    """Retained node strength (% of pre-op), averaged over the assumed regions per hemisphere."""
    ratio = np.asarray(strength_ratio, dtype=float)
    index = {name: k for k, name in enumerate(case.names)}
    return {
        domain: {
            side: 100 * float(np.mean([ratio[index[f"{side}-{key}"]] for key in keys]))
            for side in ("L", "R")
        }
        for domain, keys in ASSUMED_DOMAINS.items()
    }


def resection_scenario(
    case: CaseConnectome,
    location: str,
    radius_mm: float,
    *,
    coupling: float = 0.8,
    cut_tracts: bool = True,
) -> dict:
    """Structural loss, model FC change and assumed-domain strength for one sphere.

    Model weights are log(1 + SIFT2 weight) divided by the pre-operative spectral
    radius, as in the rest of notebook 12; removing weight cannot raise that
    radius, so the lesioned model stays stable for g below 1.
    """
    centre = centre_of(case, location)
    lesion = sphere_resection(case, centre, radius_mm, cut_tracts=cut_tracts)
    pre = case.sc["preop"]
    w_pre, w_post = model_weights(pre), model_weights(lesion["sc"])
    scale = spectral_radius(w_pre)
    fc_pre = linear_fc(w_pre / scale, coupling)[1]
    fc_post = linear_fc(w_post / scale, coupling)[1]
    strength = lesion["sc"].sum(axis=1)
    ratio = np.divide(strength, pre.sum(axis=1), out=np.ones(case.size), where=pre.sum(axis=1) > 0)
    change = fc_post - fc_pre
    np.fill_diagonal(change, 0.0)
    return {
        **lesion,
        "location": location,
        "centre_mm": centre,
        "radius_mm": float(radius_mm),
        "coupling": float(coupling),
        "cut_tracts": cut_tracts,
        "pairs_cut": int(upper(lesion["cut"] & (pre > 0)).sum()),
        "weight_removed_percent": 100 * (1 - upper(lesion["sc"]).sum() / upper(pre).sum()),
        "efficiency_percent": 100 * global_efficiency(w_post) / global_efficiency(w_pre),
        "mean_abs_fc_change": float(np.abs(upper(change)).mean()),
        "fc_change": change,
        "strength_percent": 100 * ratio,
        "domains": domain_strength(case, ratio),
    }


def proxy_calibration(case: CaseConnectome) -> dict:
    """The sphere proxy at the tumour, compared with the streamlines measured through the mask.

    The sphere has the mask's volume and sits at the tumour-weighted centre. Recall:
    share of the measured tumour-crossing weight on pairs the proxy cuts. Precision:
    share of the weight the proxy cuts that actually crossed the mask.
    """
    volume_mm3 = 1000.0 * case.provenance["tumour_mask"]["volume_ml"]
    radius = (3 * volume_mm3 / (4 * np.pi)) ** (1 / 3)
    lesion = sphere_resection(case, tumour_weighted_centre(case), radius)
    pre, tumour, cut = upper(case.sc["preop"]), upper(case.sc_tumour), upper(lesion["cut"])
    return {
        "radius_mm": float(radius),
        "centre_mm": tumour_weighted_centre(case),
        "regions_removed": [n for n, r in zip(case.names, lesion["removed"], strict=True) if r],
        "proxy_weight_removed_percent": 100 * float(pre[cut].sum() / pre.sum()),
        "measured_weight_through_mask_percent": 100 * float(tumour.sum() / pre.sum()),
        "recall_percent": 100 * float(tumour[cut].sum() / tumour.sum()),
        "precision_percent": 100 * float(tumour[cut].sum() / pre[cut].sum()),
    }


def size_location_table(
    case: CaseConnectome, locations, radii, *, coupling: float = 0.8, cut_tracts: bool = True
) -> list[dict]:
    rows = []
    for location in locations:
        for radius in radii:
            s = resection_scenario(case, location, radius, coupling=coupling, cut_tracts=cut_tracts)
            rows.append(
                {
                    "location": location,
                    "radius_mm": float(radius),
                    "regions_removed": int(s["removed"].sum()),
                    "pairs_cut": s["pairs_cut"],
                    "weight_removed_percent": s["weight_removed_percent"],
                    "efficiency_percent": s["efficiency_percent"],
                    "mean_abs_fc_change": s["mean_abs_fc_change"],
                    "domains": s["domains"],
                }
            )
    return rows


def draw_scenario(figure, case: CaseConnectome, scenario: dict) -> None:
    """Sphere and cut connections, retained strength, model FC change and assumed domains."""
    axes = figure.subplots(1, 4, gridspec_kw={"width_ratios": [1.05, 1.1, 1, 1]})
    pre = case.sc["preop"]
    xy = case.centroid_mm[:, :2]
    iu = np.triu_indices(case.size, 1)
    cutoff = np.percentile(pre[iu][pre[iu] > 0], 85)
    ax = axes[0]
    for flat in np.argsort(pre[iu]):
        i, j = iu[0][flat], iu[1][flat]
        if pre[i, j] < cutoff:
            continue
        if scenario["cut"][i, j]:
            ax.plot(*xy[[i, j]].T, color="#b2182b", lw=1.4, alpha=0.85)
        else:
            ax.plot(*xy[[i, j]].T, color="0.6", lw=0.5, alpha=0.4)
    nodes = ax.scatter(
        *xy.T, c=case.tumour_fraction, cmap="Reds", vmin=0, vmax=0.5, s=22, ec="black", lw=0.3
    )
    ax.scatter(*xy[scenario["removed"]].T, marker="x", color="black", s=40, lw=1.5)
    cx, cy, cz = scenario["centre_mm"]
    ax.add_patch(plt.Circle((cx, cy), scenario["radius_mm"], fill=False, ls="--", color="black"))
    ax.invert_xaxis()
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm, native T1w; patient right on the left)")
    ax.set_ylabel("y (mm, anterior up)")
    ax.set_title(
        f"A  r = {scenario['radius_mm']:g} mm at z = {cz:.0f} mm; red: cut", loc="left", fontsize=10
    )
    figure.colorbar(nodes, ax=ax, shrink=0.7, label="Region share inside tumour mask")
    ax = axes[1]
    order = display_order(case)
    colours = np.where(case.hemisphere[order] == "L", "#4393c3", "#d6604d")
    ax.bar(np.arange(case.size), scenario["strength_percent"][order], color=colours, width=1.0)
    ax.axvline(case.size / 2 - 0.5, color="black", lw=0.6)
    ax.set_xticks([case.size / 4, 3 * case.size / 4], ["left", "right"])
    ax.set_ylim(0, 105)
    ax.set_ylabel("Node strength retained (% of pre-op)")
    ax.set_title(
        f"B  {scenario['weight_removed_percent']:.1f}% of weight removed; "
        f"efficiency {scenario['efficiency_percent']:.1f}%",
        loc="left",
        fontsize=10,
    )
    span = max(float(np.abs(scenario["fc_change"]).max()), 1e-3)
    _matrix(
        axes[2],
        figure,
        scenario["fc_change"],
        order,
        f"C  Model FC change, g = {scenario['coupling']:g}",
        cmap="RdBu_r",
        vmin=-span,
        vmax=span,
        label="Model correlation, after − before",
    )
    ax = axes[3]
    domains = list(scenario["domains"])
    y = np.arange(len(domains))
    for offset, side, colour in ((-0.2, "L", "#4393c3"), (0.2, "R", "#d6604d")):
        values = [scenario["domains"][d][side] for d in domains]
        ax.barh(y + offset, values, height=0.4, color=colour, label=f"{side} hemisphere")
    ax.set_yticks(y, domains, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel("Mean node strength retained (% of pre-op)")
    ax.set_title("D  Assumed CANTAB regions (unsourced)", loc="left", fontsize=10)
    ax.legend(fontsize=7, loc="lower left")


@lru_cache(maxsize=1)
def _cached_case() -> CaseConnectome:
    return load_case()


def resection_explorer(location: str = TUMOUR_CENTRE, radius_mm: float = 20.0):
    """Centre, radius, tract proxy and coupling for a spherical virtual resection."""
    import ipywidgets as widgets
    from IPython.display import display

    case = _cached_case()
    style = {"description_width": "15em"}
    layout = widgets.Layout(width="38em")
    controls = {
        "location": widgets.Dropdown(
            options=[TUMOUR_CENTRE, *case.names], value=location, description="Sphere centre"
        ),
        "radius": widgets.FloatSlider(
            radius_mm, min=0.0, max=40.0, step=2.0, description="Radius r (mm)"
        ),
        "cut_tracts": widgets.Checkbox(True, description="Cut straight segments through sphere"),
        "coupling": widgets.FloatSlider(
            0.8, min=0.0, max=0.95, step=0.05, description="Coupling g"
        ),
    }
    for control in controls.values():
        control.style, control.layout, control.continuous_update = style, layout, False

    def show(location, radius, cut_tracts, coupling):
        scenario = resection_scenario(
            case, location, radius, coupling=coupling, cut_tracts=cut_tracts
        )
        figure = plt.figure(figsize=(19, 4.8), constrained_layout=True)
        draw_scenario(figure, case, scenario)
        plt.show()
        removed = [n for n, r in zip(case.names, scenario["removed"], strict=True) if r]
        print(
            f"Centre ({', '.join(f'{v:.0f}' for v in scenario['centre_mm'])}) mm; "
            f"{scenario['pairs_cut']} connected pairs cut; regions removed: "
            f"{', '.join(removed) or 'none'}"
        )

    display(widgets.interactive(show, **controls))
