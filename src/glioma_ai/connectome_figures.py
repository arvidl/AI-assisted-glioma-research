"""Figures and the record for the sub-PAT16 connectome notebook (12)."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from glioma_ai.connectome import (
    CaseConnectome,
    correlation,
    coupling_scan,
    crossing_fraction,
    fisher_standard_error,
    load_case,
    log_change,
    model_weights,
    permuted_node_scan,
    predicted_fc_change,
    shuffled_resection_null,
    upper,
    virtual_resection,
)
from glioma_ai.network import linear_fc, spectral_radius

COUPLINGS = np.round(np.arange(0.05, 0.96, 0.05), 2)
CROSSING_BINS = (0.0, 1e-9, 0.25, 0.5, 0.75, 1.0)
MIN_EDGE_WEIGHT = 10.0
SESSION_COLOURS = {"preop": "#e08214", "postop": "#542788"}


def display_order(case: CaseConnectome) -> np.ndarray:
    """Left hemisphere (subcortical, cortical) then right, for matrix display."""
    cortical = np.array([label >= 1000 for label in case.labels])
    left = case.hemisphere == "L"
    return np.concatenate(
        [np.flatnonzero(left & ~cortical), np.flatnonzero(left & cortical)]
        + [np.flatnonzero(~left & ~cortical), np.flatnonzero(~left & cortical)]
    )


def _matrix(axis, figure, values, order, title, *, cmap, vmin, vmax, label):
    image = axis.imshow(values[np.ix_(order, order)], cmap=cmap, vmin=vmin, vmax=vmax)
    half = len(order) / 2 - 0.5
    axis.axhline(half, color="black", lw=0.6)
    axis.axvline(half, color="black", lw=0.6)
    axis.set_xticks([len(order) / 4, 3 * len(order) / 4], ["left", "right"], fontsize=8)
    axis.set_yticks([len(order) / 4, 3 * len(order) / 4], ["left", "right"], fontsize=8)
    axis.set_title(title, loc="left", fontsize=10)
    figure.colorbar(image, ax=axis, shrink=0.75, label=label)


def coupling_analysis(case: CaseConnectome, coupling: float, count=200, seed=0) -> dict:
    scans = {s: coupling_scan(case.sc[s], case.fc[s], COUPLINGS) for s in case.sc}
    null = np.array(
        [permuted_node_scan(case.sc["preop"], case.fc["preop"], g, count, seed) for g in COUPLINGS]
    )
    direct = {s: correlation(upper(model_weights(case.sc[s])), upper(case.fc[s])) for s in case.sc}
    return {"scans": scans, "null": null, "direct": direct, "coupling": coupling}


def resection_analysis(case: CaseConnectome, coupling: float, count=200, seed=0) -> dict:
    pre, post = case.sc["preop"], case.sc["postop"]
    virtual = virtual_resection(case)
    measured_fc = upper(case.fc["postop"] - case.fc["preop"])
    virtual_fc = upper(predicted_fc_change(pre, virtual, coupling))
    measured_sc_fc = upper(predicted_fc_change(pre, post, coupling))
    null = shuffled_resection_null(case, coupling, count, seed)
    fraction = upper(crossing_fraction(case))
    change = upper(log_change(pre, post))
    strong = upper(pre) >= MIN_EDGE_WEIGHT
    bins = []
    for low, high in zip(CROSSING_BINS[:-1], CROSSING_BINS[1:], strict=True):
        inside = strong & (fraction >= low) & (fraction < high if high < 1 else fraction <= high)
        bins.append(
            {
                "crossing_fraction": [low, high],
                "edges": int(inside.sum()),
                "median_log2_change": float(np.median(change[inside])) if inside.any() else None,
            }
        )
    strength = {
        "measured": post.sum(axis=1) / pre.sum(axis=1),
        "virtual": virtual.sum(axis=1) / pre.sum(axis=1),
    }
    baseline = upper(case.fc["preop"])
    design = np.c_[np.ones_like(baseline), baseline]
    residual = measured_fc - design @ np.linalg.lstsq(design, measured_fc, rcond=None)[0]
    return {
        "virtual": virtual,
        "fraction": fraction,
        "change": change,
        "strong": strong,
        "bins": bins,
        "measured_fc": measured_fc,
        "virtual_fc": virtual_fc,
        "measured_sc_fc": measured_sc_fc,
        "r_virtual": correlation(virtual_fc, measured_fc),
        "r_measured_sc": correlation(measured_sc_fc, measured_fc),
        "r_change_vs_preop_fc": correlation(baseline, measured_fc),
        "r_virtual_adjusted": correlation(virtual_fc, residual),
        "null": null,
        "strength": strength,
    }


def draw_connectome(figure, case: CaseConnectome, analysis: dict) -> None:
    """Pre-operative SC, measured FC, model FC and the coupling scan with its null."""
    order = display_order(case)
    g = analysis["coupling"]
    axes = figure.subplots(1, 4, gridspec_kw={"width_ratios": [1, 1, 1, 1.15]})
    w = model_weights(case.sc["preop"])
    _matrix(
        axes[0],
        figure,
        w,
        order,
        "A  Structural, pre-op: log(1 + SIFT2)",
        cmap="viridis",
        vmin=0,
        vmax=float(w.max()),
        label="log(1 + weight)",
    )
    _matrix(
        axes[1],
        figure,
        case.fc["preop"],
        order,
        "B  Measured FC, pre-op",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        label="Pearson r (BOLD)",
    )
    _, model = linear_fc(w / spectral_radius(w), g)
    np.fill_diagonal(model, 0.0)
    span = float(np.abs(model).max())
    _matrix(
        axes[2],
        figure,
        model,
        order,
        f"C  Model FC, pre-op SC, g = {g:g}",
        cmap="RdBu_r",
        vmin=-span,
        vmax=span,
        label="Model correlation (own scale)",
    )
    ax = axes[3]
    low, high = np.percentile(analysis["null"], [2.5, 97.5], axis=1)
    ax.fill_between(COUPLINGS, low, high, color="0.85", label="pre-op, shuffled regions (95%)")
    for session, values in analysis["scans"].items():
        colour = SESSION_COLOURS[session]
        ax.plot(COUPLINGS, values, color=colour, marker="o", ms=3, label=f"{session}: model")
        ax.axhline(analysis["direct"][session], color=colour, ls="--", lw=0.9)
    ax.axvline(g, color="black", ls=":", lw=0.8)
    ax.set_xlabel("Global coupling g (dimensionless)")
    ax.set_ylabel("r(model FC, measured FC) over region pairs")
    ax.set_title("D  Structure–function agreement", loc="left", fontsize=10)
    ax.legend(fontsize=7, loc="lower right")


def draw_resection(figure, case: CaseConnectome, result: dict) -> None:
    """Tumour-crossing connections, measured SC change, and predicted vs measured FC change."""
    axes = figure.subplots(1, 4, gridspec_kw={"width_ratios": [1.05, 1, 1, 1]})
    ax = axes[0]
    pre = case.sc["preop"]
    xy = case.centroid_mm[:, :2]
    fraction = crossing_fraction(case)
    iu = np.triu_indices(case.size, 1)
    cutoff = np.percentile(pre[iu][pre[iu] > 0], 85)
    cmap = plt.get_cmap("RdYlGn_r")
    for flat in np.argsort(pre[iu]):
        i, j = iu[0][flat], iu[1][flat]
        if pre[i, j] < cutoff:
            continue
        f = fraction[i, j]
        ax.plot(*xy[[i, j]].T, color=cmap(f), lw=0.4 + 1.6 * f, alpha=0.35 + 0.6 * f)
    nodes = ax.scatter(
        *xy.T, c=case.tumour_fraction, cmap="Reds", vmin=0, vmax=0.5, s=22, ec="black", lw=0.3
    )
    ax.invert_xaxis()
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm, native T1w; patient right on the left)")
    ax.set_ylabel("y (mm, anterior up)")
    ax.set_title("A  Strongest 15% of pre-op connections", loc="left", fontsize=10)
    figure.colorbar(nodes, ax=ax, shrink=0.7, label="Region share inside tumour mask")
    ax = axes[1]
    strong = result["strong"]
    ax.scatter(result["fraction"][strong], result["change"][strong], s=5, color="0.4", alpha=0.5)
    f = np.linspace(0, 0.995, 200)
    ax.plot(f, np.log2(1 - f), color="#b2182b", label="virtual resection: log2(1 − f)")
    for b in result["bins"]:
        if b["median_log2_change"] is not None:
            low, high = b["crossing_fraction"]
            ax.hlines(b["median_log2_change"], low, max(high, 0.02), color="black", lw=2)
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylim(-8, 4)
    ax.set_xlabel("Share of pre-op weight through tumour, f")
    ax.set_ylabel("Measured log2(post / pre) structural weight")
    ax.set_title("B  Structural change per connection", loc="left", fontsize=10)
    ax.legend(fontsize=7, loc="lower left")
    ax = axes[2]
    ax.scatter(result["virtual_fc"], result["measured_fc"], s=4, color="#2166ac", alpha=0.4)
    ax.axhline(0, color="black", lw=0.6)
    ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel("Model FC change, virtual resection")
    ax.set_ylabel("Measured FC change (post − pre, r)")
    title = f"C  Predicted vs measured, r = {result['r_virtual']:.2f}"
    ax.set_title(title, loc="left", fontsize=10)
    ax = axes[3]
    ax.hist(result["null"], bins=30, color="0.75", label="tumour pattern on random pairs")
    ax.axvline(result["r_virtual"], color="#2166ac", lw=2, label="virtual resection")
    ax.axvline(result["r_measured_sc"], color="#542788", lw=2, ls="--", label="measured post-op SC")
    values = np.r_[result["null"], result["r_virtual"], result["r_measured_sc"]]
    ax.set_xlim(values.min() - 0.03, values.max() + 0.03)
    ax.set_xlabel("r(model FC change, measured FC change)")
    ax.set_ylabel("Shuffles")
    ax.set_title("D  Against a placement null", loc="left", fontsize=10)
    ax.legend(fontsize=7)


def write_connectome_experiment(
    output: Path, *, coupling: float = 0.8, count: int = 200, case: CaseConnectome | None = None
) -> dict:
    """Figures and record for notebook 12 from the tracked sub-PAT16 matrices."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    case = case or load_case()
    coupling_result = coupling_analysis(case, coupling, count)
    resection = resection_analysis(case, coupling, count)
    figure = plt.figure(figsize=(19, 4.6), constrained_layout=True)
    draw_connectome(figure, case, coupling_result)
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"pat16_connectome.{suffix}", dpi=160)
    plt.close(figure)
    figure = plt.figure(figsize=(19, 4.6), constrained_layout=True)
    draw_resection(figure, case, resection)
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"pat16_resection.{suffix}", dpi=160)
    plt.close(figure)
    k = int(np.argmin(np.abs(COUPLINGS - coupling)))
    null = resection["null"]
    sessions = case.provenance["sessions"]
    iu = np.triu_indices(case.size, 1)
    record = {
        "evidence_type": "real_data_single_case_descriptive",
        "case": case.provenance["case"],
        "upstream_qc": case.provenance["upstream_qc"],
        "structural": {
            s: {
                "total_weight": float(case.sc[s][iu].sum()),
                "connected_pairs_percent": round(100 * float((case.sc[s][iu] > 0).mean()), 1),
                "assigned_weight_percent": round(100 * sessions[s]["assigned_weight_fraction"], 1),
            }
            for s in case.sc
        },
        "bold": {s: sessions[s]["bold"] for s in sessions},
        "fisher_se_lower_bound": {
            s: round(fisher_standard_error(sessions[s]["bold"]["clean_volumes"]), 3)
            for s in sessions
        },
        "model": {
            "dynamics": "dx/dt = -x + g W x + sigma xi; exact stationary correlation",
            "weights": "W = log(1 + SIFT2 weight) / spectral radius of the pre-op W",
            "coupling_g": coupling,
        },
        "structure_function": {
            s: {
                "r_at_g": round(float(v[k]), 3),
                "best_g": float(COUPLINGS[int(np.argmax(v))]),
                "best_r": round(float(v.max()), 3),
                "direct_r_log_sc_vs_fc": round(coupling_result["direct"][s], 3),
            }
            for s, v in coupling_result["scans"].items()
        },
        "preop_shuffled_region_null_at_g": {
            "count": count,
            "percentile_97_5": round(float(np.percentile(coupling_result["null"][k], 97.5)), 3),
        },
        "tumour": {
            "mask_volume_ml": round(case.provenance["tumour_mask"]["volume_ml"], 1),
            "preop_weight_through_tumour_percent": round(
                100 * float(case.sc_tumour[iu].sum() / case.sc["preop"][iu].sum()), 1
            ),
            "regions_over_10_percent_inside": [
                n for n, f in zip(case.names, case.tumour_fraction, strict=True) if f > 0.1
            ],
        },
        "structural_change_by_crossing": resection["bins"],
        "min_edge_weight_for_bins": MIN_EDGE_WEIGHT,
        "fc_change_agreement": {
            "r_virtual_resection": round(resection["r_virtual"], 3),
            "r_measured_postop_sc": round(resection["r_measured_sc"], 3),
            "r_measured_change_vs_preop_fc": round(resection["r_change_vs_preop_fc"], 3),
            "r_virtual_after_regressing_preop_fc": round(resection["r_virtual_adjusted"], 3),
            "pre_post_fc_similarity_r": round(
                correlation(upper(case.fc["preop"]), upper(case.fc["postop"])), 3
            ),
            "placement_null": {
                "count": count,
                "median": round(float(np.median(null)), 3),
                "percentile_97_5": round(float(np.percentile(null, 97.5)), 3),
                "p_one_sided_virtual": round(
                    float((1 + np.sum(null >= resection["r_virtual"])) / (1 + count)), 3
                ),
            },
        },
        "node_strength_ratio_correlation": round(
            correlation(resection["strength"]["virtual"], resection["strength"]["measured"]), 3
        ),
        "interpretation": "one patient, upstream QC pending; descriptive, not validation",
    }
    (output / "pat16_connectome.json").write_text(json.dumps(record, indent=2) + "\n")
    return record
