"""Generate synthetic imaging, dynamics, and evidence examples on CPU."""

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from glioma_ai.biology_examples import neuron_glioma_example, niche_example
from glioma_ai.growth import integrate_fisher_2d
from glioma_ai.metrics import dice_score, relative_volume_error, volume_ml
from glioma_ai.neuroglial_examples import astrocyte_example, lfp_field_example
from glioma_ai.provenance import environment_record, sha256
from glioma_ai.published import write_published_imaging_reference

SYNTHETIC_LABELS = {
    "background": 0,
    "necrosis_or_non_enhancing": 1,
    "edema_or_FLAIR_abnormality": 2,
    "enhancing_tumor": 4,
}
COMPARTMENT_COLORS = {0: "#f7f7f7", 1: "#7467a5", 2: "#59a6ae", 4: "#d67645"}
COMPARTMENT_NAMES = {
    1: "1  necrotic core / non-enhancing",
    2: "2  edema / FLAIR abnormality",
    4: "4  enhancing tumor",
}
PERTURBATION_COLORS = {"translated": "#c2185b", "expanded": "#1f5fbf"}


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def _save_figure(figure, output: Path, stem: str) -> None:
    figure.savefig(output / f"{stem}.png", dpi=180, bbox_inches="tight")
    figure.savefig(output / f"{stem}.pdf", bbox_inches="tight")
    plt.close(figure)


def imaging_example(output: Path) -> dict:
    """A constructed contour can change volume and overlap differently."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    shape = (64, 64, 40)
    spacing = np.array([1.2, 1.2, 2.0])
    grid = np.indices(shape, dtype=float)
    center = (np.array(shape) - 1) / 2
    position = (grid - center[:, None, None, None]) * spacing[:, None, None, None]
    q = sum((position[axis] / radius) ** 2 for axis, radius in enumerate((10, 12, 16)))
    reference = q <= 1
    translated = np.roll(reference, 4, axis=0)
    expanded = q <= 1.12**2
    # Nested like a typical glioblastoma: necrotic core, enhancing rim, edema.
    labels = np.zeros(shape, dtype=np.uint8)
    labels[reference] = 2
    labels[q <= 0.7**2] = 4
    labels[q <= 0.4**2] = 1
    affine = np.diag([*spacing, 1.0])
    for stem, values in (
        ("synthetic_labels", labels),
        ("synthetic_reference", reference.astype(np.uint8)),
        ("synthetic_expanded", expanded.astype(np.uint8)),
    ):
        image = nib.Nifti1Image(values, affine)
        image.header.set_xyzt_units("mm")
        nib.save(image, output / f"{stem}.nii.gz")
    ref_ml = volume_ml(reference, affine)
    summary = {
        "evidence_type": "synthetic",
        "coordinate_space": "constructed grid, affine expressed in mm",
        "voxel_spacing_mm": spacing.tolist(),
        "shape": list(shape),
        "labels": SYNTHETIC_LABELS,
        "label_meaning": "constructed compartments, not histologically observed tissue",
        "translation_mm": 4 * float(spacing[0]),
        "radius_expansion_percent": 12,
        "reference_volume_ml": ref_ml,
        "translated_dice": dice_score(translated, reference),
        "expanded_dice": dice_score(expanded, reference),
        "expanded_volume_ml": volume_ml(expanded, affine),
        "expanded_relative_volume_error": relative_volume_error(
            volume_ml(expanded, affine), ref_ml
        ),
        "volume_by_label_ml": {
            str(label): volume_ml(labels == label, affine) for label in (1, 2, 4)
        },
        "imaging_model_run": False,
        "clinical_response": "not_assessed",
    }
    plane = shape[2] // 2
    plane_mm = (plane - center[2]) * spacing[2]
    half = (np.array(shape[:2]) * spacing[:2]) / 2
    extent = [-half[0], half[0], -half[1], half[1]]
    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.6), constrained_layout=True)

    axes[0].imshow(
        labels[:, :, plane].T,
        origin="lower",
        extent=extent,
        cmap=ListedColormap(
            [COMPARTMENT_COLORS[0], COMPARTMENT_COLORS[1], COMPARTMENT_COLORS[2], "#ffffff"]
            + [COMPARTMENT_COLORS[4]]
        ),
        vmin=0,
        vmax=4,
        interpolation="nearest",
    )
    axes[0].legend(
        handles=[
            Patch(color=COMPARTMENT_COLORS[label], label=COMPARTMENT_NAMES[label])
            for label in (1, 4, 2)
        ],
        loc="upper left",
        fontsize=8,
        title="Label (construction)",
        title_fontsize=8,
    )
    axes[0].set_title(f"A  Nested compartments, mid-plane z = {plane_mm:+.0f} mm", loc="left")

    axes[1].imshow(
        reference[:, :, plane].T,
        origin="lower",
        extent=extent,
        cmap=ListedColormap(["#ffffff", "#c9c9c9"]),
        interpolation="nearest",
    )
    x_mm = (np.arange(shape[0]) - center[0]) * spacing[0]
    y_mm = (np.arange(shape[1]) - center[1]) * spacing[1]
    for mask, color in (
        (translated, PERTURBATION_COLORS["translated"]),
        (expanded, PERTURBATION_COLORS["expanded"]),
    ):
        axes[1].contour(
            x_mm, y_mm, mask[:, :, plane].T, levels=[0.5], colors=[color], linewidths=1.8
        )
    shift = summary["translation_mm"]
    axes[1].legend(
        handles=[
            Patch(color="#c9c9c9", label="Reference whole tumor (labels 1+2+4)"),
            Line2D(
                [],
                [],
                color=PERTURBATION_COLORS["translated"],
                lw=1.8,
                label=f"Translated {shift:.1f} mm along x",
            ),
            Line2D(
                [],
                [],
                color=PERTURBATION_COLORS["expanded"],
                lw=1.8,
                label="Each radius expanded 12%",
            ),
        ],
        loc="upper left",
        fontsize=8,
    )
    axes[1].set_title("B  Two perturbed whole-tumor contours", loc="left")
    for axis in axes[:2]:
        axis.set_xlabel("x (mm from ellipsoid centre)")
        axis.set_ylabel("y (mm from ellipsoid centre)")
        axis.set_xlim(-26, 26)
        axis.set_ylim(-26, 26)

    volumes = [ref_ml, volume_ml(translated, affine), summary["expanded_volume_ml"]]
    dices = [1.0, summary["translated_dice"], summary["expanded_dice"]]
    bars = axes[2].bar(
        ["Reference", "Translated", "Expanded"],
        volumes,
        color=["#c9c9c9", PERTURBATION_COLORS["translated"], PERTURBATION_COLORS["expanded"]],
        edgecolor="#333333",
    )
    for bar, value, dice in zip(bars, volumes, dices, strict=True):
        error = 100 * (value - ref_ml) / ref_ml
        axes[2].annotate(
            f"{value:.2f} mL\nΔV {error:+.1f}%\nDice {dice:.3f}",
            (bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    axes[2].set_ylim(0, 1.35 * max(volumes))
    axes[2].set_ylabel("Whole-tumor volume (mL)")
    axes[2].set_title("C  Volume error and overlap disagree", loc="left")
    figure.suptitle("Synthetic construction: no patient data and no model inference")
    _save_figure(figure, output, "imaging")
    write_json(output / "imaging.json", summary)
    return summary


def dynamics_example(output: Path) -> dict:
    """Compare two prescribed PDE trajectories with a fixed initial mask."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    spacing_mm, dt_days, n_steps = 1.0, 0.25, 80
    diffusion, proliferation = 0.35, 0.035
    coordinates = np.arange(81, dtype=float) - 40
    x, y = np.meshgrid(coordinates, coordinates, indexing="ij")
    initial = (x * x + y * y <= 7**2).astype(float)
    density = integrate_fisher_2d(
        initial, diffusion, proliferation, spacing_mm, spacing_mm, dt_days, n_steps
    )
    alternative = integrate_fisher_2d(
        initial, 2 * diffusion, proliferation, spacing_mm, spacing_mm, dt_days, n_steps
    )
    threshold = 0.5
    initial_binary = initial.astype(bool)
    summary = {
        "evidence_type": "synthetic",
        "state": "constructed normalized density, not an MRI intensity",
        "equation": "dc/dt = div(D grad c) + rho c (1-c)",
        "boundary": "no flux",
        "solver": "explicit finite difference",
        "parameters": {
            "diffusivity_mm2_per_day": diffusion,
            "proliferation_per_day": proliferation,
            "spacing_mm": spacing_mm,
            "dt_days": dt_days,
            "n_steps": n_steps,
            "elapsed_days": dt_days * n_steps,
        },
        "thresholds": [0.5, 0.05],
        "initial_area_mm2": int(initial_binary.sum()),
        "area_at_threshold_05_mm2": int((density >= threshold).sum()),
        "area_at_threshold_005_mm2": int((density >= 0.05).sum()),
        "alternative_area_at_threshold_05_mm2": int((alternative >= threshold).sum()),
        "density_min": float(density.min()),
        "density_max": float(density.max()),
        "overlap_with_initial": dice_score(
            (density >= threshold)[:, :, None], initial_binary[:, :, None]
        ),
        "alternative_diffusivity_mm2_per_day": 2 * diffusion,
        "inverse_estimation": "not_performed",
        "recurrence_prediction": "not_performed",
        "clinical_response": "not_assessed",
    }
    figure, axes = plt.subplots(1, 3, figsize=(10.5, 3.8), constrained_layout=True)
    for axis, values, title in zip(
        axes,
        (initial, density, alternative),
        ("Initial construction", "Prescribed D = 0.35", "Prescribed D = 0.70"),
        strict=True,
    ):
        axis.imshow(
            values.T,
            origin="lower",
            extent=(-40.5, 40.5, -40.5, 40.5),
            cmap="magma",
            vmin=0,
            vmax=1,
        )
        if values is not initial:
            axis.contour(
                coordinates,
                coordinates,
                values.T,
                levels=[0.05, 0.5],
                colors=["#88d9e6", "#ffffff"],
                linewidths=1,
            )
        axis.set_title(title)
        axis.set_xlabel("Synthetic x (mm)")
        axis.set_ylabel("Synthetic y (mm)")
        axis.set_xlim(-22, 22)
        axis.set_ylim(-22, 22)
    figure.suptitle("Synthetic density after 20 days — coefficients are prescribed")
    _save_figure(figure, output, "dynamics")
    write_json(output / "dynamics.json", summary)
    np.savez_compressed(output / "synthetic_density.npz", initial=initial, density=density)
    return summary


def run_demo(output: Path, paper_dir: Path | None = None) -> dict:
    """Write measurement, biology, and evidence constructions with provenance."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    results = {
        "imaging": imaging_example(output),
        "dynamics": dynamics_example(output),
        "microenvironment": niche_example(output),
        "neuron_glioma": neuron_glioma_example(output),
        "astrocyte_potassium": astrocyte_example(output),
        "lfp_field": lfp_field_example(output),
        "assistant_endpoints": {
            "productivity": "not_measured",
            "scientific_quality": "not_measured",
            "clinical_utility": "not_measured",
        },
    }
    write_json(output / "metrics.json", results)
    published = write_published_imaging_reference(output, paper_dir)
    files = [
        "metrics.json",
        "imaging.json",
        "dynamics.json",
        "imaging.png",
        "imaging.pdf",
        "dynamics.png",
        "dynamics.pdf",
        "synthetic_labels.nii.gz",
        "synthetic_reference.nii.gz",
        "synthetic_expanded.nii.gz",
        "synthetic_density.npz",
        "microenvironment.json",
        "microenvironment.png",
        "microenvironment.pdf",
        "synthetic_niche.npz",
        "neuron_glioma.json",
        "neuron_glioma.png",
        "neuron_glioma.pdf",
        "neuron_glioma_sensitivity.png",
        "neuron_glioma_sensitivity.pdf",
        "synthetic_neuron_glioma.npz",
        "neuron_glioma_traces.tsv",
        "microenvironment_talk.png",
        "microenvironment_talk.pdf",
        "neuron_glioma_talk.png",
        "neuron_glioma_talk.pdf",
        "astrocyte_potassium.json",
        "astrocyte_potassium.png",
        "astrocyte_potassium.pdf",
        "synthetic_potassium.npz",
        "lfp_field.json",
        "lfp_field.png",
        "lfp_field.pdf",
        "synthetic_lfp_field.npz",
    ]
    record = {
        **environment_record(),
        "evidence_type": "synthetic",
        "inputs": (
            "constructed in glioma_ai.demo and glioma_ai.biology_examples; "
            "no external data or model"
        ),
        "parameters": {
            "imaging": results["imaging"],
            "dynamics": results["dynamics"]["parameters"],
            "microenvironment": results["microenvironment"]["parameters"],
            "neuron_glioma": results["neuron_glioma"]["parameters"],
            "astrocyte_potassium": results["astrocyte_potassium"]["parameters"],
            "lfp_field": results["lfp_field"]["parameters"],
        },
        "output_sha256": {name: sha256(output / name) for name in files},
        "related_published_evidence": {
            "file": "published_imaging_reference.json",
            "sha256": sha256(output / "published_imaging_reference.json"),
            "evidence_type": published["evidence_type"],
            "doi": published["doi"],
            "inference_rerun": False,
        },
    }
    write_json(output / "run.json", record)
    if paper_dir is not None:
        paper_dir = Path(paper_dir)
        paper_dir.mkdir(parents=True, exist_ok=True)
        for name in (
            "imaging",
            "dynamics",
            "microenvironment",
            "neuron_glioma",
            "neuron_glioma_sensitivity",
            "microenvironment_talk",
            "neuron_glioma_talk",
            "astrocyte_potassium",
            "lfp_field",
        ):
            shutil.copy2(output / f"{name}.pdf", paper_dir / f"{name}.pdf")
        image, dynamics = results["imaging"], results["dynamics"]
        niche, neural = results["microenvironment"], results["neuron_glioma"]
        potassium, fields = results["astrocyte_potassium"], results["lfp_field"]
        integral = neural["final_density_integral_mm2"]
        macros = {
            "ExampleReferenceML": f"{image['reference_volume_ml']:.3f}",
            "ExampleTranslatedDice": f"{image['translated_dice']:.3f}",
            "ExampleExpandedDice": f"{image['expanded_dice']:.3f}",
            "ExampleExpandedPercent": f"{100 * image['expanded_relative_volume_error']:.2f}",
            "ExampleInitialArea": str(dynamics["initial_area_mm2"]),
            "ExampleVisibleArea": str(dynamics["area_at_threshold_05_mm2"]),
            "ExampleLowArea": str(dynamics["area_at_threshold_005_mm2"]),
            "ExampleAlternativeArea": str(dynamics["alternative_area_at_threshold_05_mm2"]),
            "ExampleNicheFractionPercent": f"{100 * niche['final_mes_like_fraction']:.2f}",
            "ExampleNicheNoCuePercent": f"{100 * niche['no_cue_final_mes_like_fraction']:.2f}",
            "ExampleNeuralBaselineIntegral": f"{integral['baseline']:.2f}",
            "ExampleNeuralOneWayIntegral": f"{integral['one_way']:.2f}",
            "ExampleNeuralFeedbackIntegral": f"{integral['feedback']:.2f}",
            "ExampleNeuralFeedbackRatio": f"{neural['feedback_to_baseline_integral_ratio']:.2f}",
            "ExampleNeuralFeedbackOverOneWayPercent": (
                f"{100 * (neural['feedback_to_one_way_integral_ratio'] - 1):.2f}"
            ),
            "ExampleNeuralStepDifferencePercent": (
                f"{100 * neural['step_halving_relative_integral_difference']:.3f}"
            ),
            "ExampleKReferencePeak": f"{potassium['peak_excess_K_mM']['reference']:.3f}",
            "ExampleKReducedPeak": f"{potassium['peak_excess_K_mM']['reduced']:.3f}",
            "ExampleKReferenceShift": (
                f"{potassium['peak_K_equilibrium_shift_mV']['reference']:.2f}"
            ),
            "ExampleKReducedShift": f"{potassium['peak_K_equilibrium_shift_mV']['reduced']:.2f}",
            "ExampleFieldLong": f"{fields['peak_analytic_field_V_per_m'][0]:.3f}",
            "ExampleFieldShort": f"{fields['peak_analytic_field_V_per_m'][1]:.3f}",
        }
        (paper_dir / "numbers.tex").write_text(
            "% Generated from synthetic code; no patient results.\n"
            + "".join(
                "\\newcommand{\\" + key + "}{" + value + "}\n" for key, value in macros.items()
            )
        )
    return results
