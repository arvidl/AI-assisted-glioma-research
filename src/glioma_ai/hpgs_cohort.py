"""Dataset-reference versus published-model masks from a local companion checkout.

Reads UCSF-PDGM reference segmentations and the SegResNet label maps that the
companion study (Lundervold et al. 2026) produced for its 50-subject evaluation
cohort. Nothing is downloaded, registered, resampled or relabeled; mismatched
geometry or unknown labels are errors. Outputs belong in ignored local storage.
"""

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from glioma_ai.demo import COMPARTMENT_COLORS
from glioma_ai.metrics import dice_score, volume_ml
from glioma_ai.published import published_imaging_reference

LABELS = {1: "NCR  necrotic tumor core", 2: "ED  peritumoral edema", 4: "ET  enhancing tumor"}
REGIONS = {"WT": (1, 2, 4), "TC": (1, 4), "ET": (4,)}
REGION_COLORS = {"WT": "#333333", "TC": "#7467a5", "ET": "#d67645"}
COHORT = Path("data/derivatives_cohort50")
IMAGES = Path("data/ucsf_pdgm_cohort50")
EXPECTED_AXES = ("L", "P", "S")


def companion_checkout(repo_root: Path | None = None) -> Path | None:
    """Return the companion checkout from HPGS_REPO or ignored local/hpgs.json."""
    value = os.environ.get("HPGS_REPO")
    if not value and repo_root is not None:
        config = Path(repo_root) / "local/hpgs.json"
        if config.is_file():
            value = json.loads(config.read_text()).get("checkout")
    if not value:
        return None
    root = Path(value)
    return root if (root / COHORT).is_dir() and (root / IMAGES).is_dir() else None


def _paths(checkout: Path, subject: str) -> dict[str, Path]:
    return {
        "reference": checkout / IMAGES / f"sub-{subject}/sub-{subject}_tumor_segmentation.nii.gz",
        "t1c": checkout / IMAGES / f"sub-{subject}/sub-{subject}_T1c_bias.nii.gz",
        "prediction": checkout
        / COHORT
        / f"sub-{subject}/seg_dl/sub-{subject}_seg_brats3_dl.nii.gz",
        "metrics": checkout / COHORT / f"sub-{subject}/metrics/sub-{subject}_metrics_dl_vs_gt.json",
    }


def cohort_subjects(checkout: Path) -> list[str]:
    """Subjects with a reference, a model label map and a companion metrics record."""
    subjects = []
    for directory in sorted((checkout / COHORT).glob("sub-*")):
        subject = directory.name.removeprefix("sub-")
        paths = _paths(checkout, subject)
        if all(paths[key].is_file() for key in ("reference", "prediction", "metrics")):
            subjects.append(subject)
    return subjects


def _labels(path: Path) -> tuple[np.ndarray, np.ndarray]:
    image = nib.load(path)
    values = np.asarray(image.dataobj)
    if not np.all(np.isin(np.unique(values), (0, *LABELS))):
        raise ValueError(f"Unknown labels in {path.name}; expected 0, 1, 2 and 4.")
    return values.astype(np.uint8), image.affine


def load_pair(checkout: Path, subject: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reference labels, model labels and their shared affine, without resampling."""
    paths = _paths(checkout, subject)
    reference, affine = _labels(paths["reference"])
    prediction, predicted_affine = _labels(paths["prediction"])
    if reference.shape != prediction.shape or not np.allclose(affine, predicted_affine):
        raise ValueError(f"Reference and model geometry differ for subject {subject}.")
    if nib.aff2axcodes(affine) != EXPECTED_AXES:
        raise ValueError(f"Subject {subject} is not stored as {EXPECTED_AXES}.")
    return reference, prediction, affine


def region_metrics(reference: np.ndarray, prediction: np.ndarray, affine: np.ndarray) -> dict:
    """Dice and signed volume error per evaluated region (WT, TC, ET)."""
    result = {}
    for region, labels in REGIONS.items():
        truth, model = np.isin(reference, labels), np.isin(prediction, labels)
        reference_ml, model_ml = volume_ml(truth, affine), volume_ml(model, affine)
        result[region] = {
            "dice": dice_score(model, truth),
            "reference_ml": reference_ml,
            "model_ml": model_ml,
            "volume_error_percent": (
                100 * (model_ml - reference_ml) / reference_ml if reference_ml else None
            ),
        }
    return result


def cohort_table(checkout: Path) -> dict:
    """Per-subject measurements, checked against the companion's own Dice records."""
    rows, largest_difference = [], 0.0
    for subject in cohort_subjects(checkout):
        reference, prediction, affine = load_pair(checkout, subject)
        metrics = region_metrics(reference, prediction, affine)
        recorded = json.loads(_paths(checkout, subject)["metrics"].read_text())["metrics"]
        for region in REGIONS:
            largest_difference = max(
                largest_difference, abs(metrics[region]["dice"] - recorded[region]["dice"])
            )
        rows.append({"subject": subject, **metrics})
    if largest_difference > 1e-6:
        raise ValueError(f"Recomputed Dice differs from the companion by {largest_difference}.")
    medians = {}
    for region in REGIONS:
        defined = [row[region] for row in rows if row[region]["volume_error_percent"] is not None]
        errors = np.array([value["volume_error_percent"] for value in defined])
        medians[region] = {
            "n_with_reference": len(defined),
            "n_model_smaller": int((errors < 0).sum()),
            "n_abs_volume_error_ge_40_percent": int((np.abs(errors) >= 40).sum()),
            "dice": float(np.median([value["dice"] for value in defined])),
            "volume_error_percent": float(
                np.median([value["volume_error_percent"] for value in defined])
            ),
        }
    published = published_imaging_reference()["evaluation"]["median_dice"]
    published_dice = {
        "WT": published["whole_tumor"],
        "TC": published["tumor_core"],
        "ET": published["enhancing_tumor"],
    }
    return {
        "published_median_dice": published_dice,
        "medians_match_published_at_two_decimals": all(
            round(medians[region]["dice"], 2) == round(published_dice[region], 2)
            for region in REGIONS
        ),
        "evidence_type": "real_data_local_recomputation",
        "dataset": "UCSF-PDGM v5 (Calabrese et al. 2022; TCIA, doi:10.7937/tcia.bdgf-8v37)",
        "licence": "CC BY 4.0; TCIA Data Usage Policy applies",
        "reference": "dataset-provided tumor segmentation",
        "model": "MONAI BraTS SegResNet label maps produced by the companion study",
        "publication": "https://doi.org/10.1080/03091902.2026.2713703",
        "n_subjects": len(rows),
        "max_dice_difference_vs_companion": largest_difference,
        "medians": medians,
        "rows": rows,
        "inference_rerun_here": False,
    }


def median_case(table: dict) -> str:
    """Subject whose whole-tumor Dice is closest to the cohort median (ties: lowest ID)."""
    target = table["medians"]["WT"]["dice"]
    return min(table["rows"], key=lambda row: (abs(row["WT"]["dice"] - target), row["subject"]))[
        "subject"
    ]


def write_cohort_figure(checkout: Path, table: dict, synthetic: dict, output: Path) -> dict:
    """Case overlay, model-versus-reference contours and the cohort Dice/volume scatter."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    subject = median_case(table)
    reference, prediction, affine = load_pair(checkout, subject)
    t1c = np.asarray(nib.load(_paths(checkout, subject)["t1c"]).dataobj, dtype=float)
    if t1c.shape != reference.shape:
        raise ValueError("T1c and segmentation grids differ.")
    slice_index = int(np.argmax(np.isin(reference, REGIONS["WT"]).sum(axis=(0, 1))))
    z_mm = float((affine @ [0, 0, slice_index, 1])[2])
    spacing = np.abs(np.diag(affine)[:3])
    case = next(row for row in table["rows"] if row["subject"] == subject)

    background = t1c[:, :, slice_index].T
    low, high = np.percentile(background[background > 0], [1, 99])
    labels_slice = reference[:, :, slice_index].T
    rows, cols = np.nonzero(np.isin(labels_slice, REGIONS["WT"]))
    margin = 25
    window = (
        slice(max(rows.min() - margin, 0), rows.max() + margin),
        slice(max(cols.min() - margin, 0), cols.max() + margin),
    )
    extent_mm = [
        window[1].start * spacing[0],
        window[1].stop * spacing[0],
        window[0].stop * spacing[1],
        window[0].start * spacing[1],
    ]

    figure, axes = plt.subplots(1, 3, figsize=(17, 5.4), constrained_layout=True)
    for axis in axes[:2]:
        axis.imshow(background[window], cmap="gray", vmin=low, vmax=high, extent=extent_mm)
        axis.set_xlabel("x (mm, voxel axis i; image right = patient left)")
        axis.set_ylabel("y (mm, voxel axis j; image bottom = posterior)")
        for text, position in (
            ("R", (0.02, 0.5)),
            ("L", (0.96, 0.5)),
            ("A", (0.5, 0.95)),
            ("P", (0.5, 0.02)),
        ):
            axis.text(
                *position,
                text,
                transform=axis.transAxes,
                color="white",
                fontsize=10,
                fontweight="bold",
                ha="center",
                va="center",
            )

    overlay = np.ma.masked_equal(labels_slice[window], 0)
    axes[0].imshow(
        overlay,
        cmap=ListedColormap(
            [COMPARTMENT_COLORS[1], COMPARTMENT_COLORS[2], "#ffffff", COMPARTMENT_COLORS[4]]
        ),
        vmin=1,
        vmax=4,
        alpha=0.55,
        extent=extent_mm,
        interpolation="nearest",
    )
    axes[0].legend(
        handles=[
            Patch(color=COMPARTMENT_COLORS[label], label=LABELS[label]) for label in (1, 4, 2)
        ],
        loc="lower left",
        fontsize=8,
        title="Dataset reference labels",
        title_fontsize=8,
    )
    axes[0].set_title(f"A  UCSF-PDGM-{subject}, T1c, axial z = {z_mm:.0f} mm", loc="left")

    x_mm = (np.arange(window[1].start, window[1].stop) + 0.5) * spacing[0]
    y_mm = (np.arange(window[0].start, window[0].stop) + 0.5) * spacing[1]
    styles = {"WT": "#ffd400", "ET": "#ff4d4d"}
    for region, color in styles.items():
        for labels, style in ((reference, "solid"), (prediction, "dashed")):
            mask = np.isin(labels[:, :, slice_index].T, REGIONS[region])[window]
            if mask.any():
                axes[1].contour(
                    x_mm, y_mm, mask, levels=[0.5], colors=[color], linestyles=style, linewidths=1.6
                )
    axes[1].legend(
        handles=[
            Line2D([], [], color=styles["WT"], lw=1.6, label="WT reference"),
            Line2D([], [], color=styles["WT"], lw=1.6, ls="--", label="WT model"),
            Line2D([], [], color=styles["ET"], lw=1.6, label="ET reference"),
            Line2D([], [], color=styles["ET"], lw=1.6, ls="--", label="ET model"),
        ],
        loc="lower left",
        fontsize=8,
    )
    axes[1].set_title(
        "B  Model vs reference contours, same slice\n"
        f"WT Dice {case['WT']['dice']:.2f}, ΔV {case['WT']['volume_error_percent']:+.1f}%;  "
        f"ET Dice {case['ET']['dice']:.2f}, ΔV {case['ET']['volume_error_percent']:+.1f}%",
        loc="left",
        fontsize=10,
    )

    limit = 100.0
    off_scale = []
    for region, color in REGION_COLORS.items():
        defined = [
            (row["subject"], row[region])
            for row in table["rows"]
            if row[region]["volume_error_percent"] is not None
        ]
        shown = [value for _, value in defined if abs(value["volume_error_percent"]) <= limit]
        axes[2].scatter(
            [value["dice"] for value in shown],
            [value["volume_error_percent"] for value in shown],
            s=22,
            color=color,
            alpha=0.75,
            label=f"{region} (n = {len(defined)})",
        )
        for subject_id, value in defined:
            if abs(value["volume_error_percent"]) > limit:
                off_scale.append((subject_id, region, color, value))
        axes[2].scatter(
            case[region]["dice"],
            case[region]["volume_error_percent"],
            s=110,
            facecolors="none",
            edgecolors=color,
            linewidths=1.6,
        )
    axes[2].scatter(
        [synthetic["translated_dice"], synthetic["expanded_dice"]],
        [0.0, 100 * synthetic["expanded_relative_volume_error"]],
        marker="*",
        s=180,
        color=["#c2185b", "#1f5fbf"],
        edgecolors="black",
        zorder=3,
    )
    axes[2].annotate(
        "synthetic shift",
        (synthetic["translated_dice"], 0.0),
        xytext=(6, 6),
        textcoords="offset points",
        fontsize=8,
    )
    axes[2].annotate(
        "synthetic 12% expansion",
        (synthetic["expanded_dice"], 100 * synthetic["expanded_relative_volume_error"]),
        xytext=(-10, 8),
        textcoords="offset points",
        fontsize=8,
        ha="right",
    )
    axes[2].axhline(0, color="#999999", lw=0.8)
    for threshold in (40, -65):
        axes[2].axhline(threshold, color="#999999", lw=0.8, ls=":")
    axes[2].text(
        0.02,
        40,
        "+40% (RANO 2.0 volumetric progression)",
        fontsize=7,
        va="bottom",
        transform=axes[2].get_yaxis_transform(),
    )
    axes[2].text(
        0.02,
        -65,
        "−65% (RANO 2.0 volumetric partial response)",
        fontsize=7,
        va="bottom",
        transform=axes[2].get_yaxis_transform(),
    )
    for index, (subject_id, region, color, value) in enumerate(off_scale):
        y = np.sign(value["volume_error_percent"]) * (limit - 4)
        axes[2].scatter(value["dice"], y, marker="^" if y > 0 else "v", s=60, color=color)
        axes[2].annotate(
            f"off scale: {subject_id} {region} {value['volume_error_percent']:+.0f}% "
            f"({value['reference_ml']:.1f} → {value['model_ml']:.1f} mL)",
            (value["dice"], y),
            xytext=(8, -12 * index - 4),
            textcoords="offset points",
            fontsize=7,
            va="top",
        )
    axes[2].set_ylim(-limit, limit)
    axes[2].set_xlim(0.15, 1.0)
    axes[2].set_xlabel("Dice (model vs dataset reference)")
    axes[2].set_ylabel("Signed volume error, model − reference (%)")
    axes[2].set_title("C  Cohort: overlap vs volume error per subject", loc="left")
    axes[2].legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        fontsize=8,
        title="Region\n(open circle: case in A–B;\nstars: synthetic, Fig. 1)",
        title_fontsize=8,
    )
    figure.suptitle(
        "Real data: UCSF-PDGM reference labels vs the published SegResNet model "
        "(Lundervold et al. 2026); recomputed locally, no new inference"
    )
    figure.savefig(output / "hpgs_cohort.png", dpi=180, bbox_inches="tight")
    plt.close(figure)
    record = {key: value for key, value in table.items() if key != "rows"}
    record.update(
        {
            "case": subject,
            "slice_index": slice_index,
            "slice_z_mm": z_mm,
            "case_metrics": {region: case[region] for region in REGIONS},
        }
    )
    (output / "hpgs_cohort.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def cohort_caption(record: dict, figure_number: int = 3) -> str:
    """Paper-style Markdown caption filled from a locally computed record."""
    case, medians, n = record["case_metrics"], record["medians"], record["n_subjects"]
    agreement = "agree with" if record["medians_match_published_at_two_decimals"] else "differ from"

    def change(region: str) -> str:
        value = case[region]
        return (
            f"Dice {value['dice']:.2f}, volume {value['reference_ml']:.1f} → "
            f"{value['model_ml']:.1f} mL (ΔV {value['volume_error_percent']:+.1f}%)"
        )

    def median(region: str) -> str:
        value = medians[region]
        return f"{region} Dice {value['dice']:.3f} (ΔV {value['volume_error_percent']:+.1f}%)"

    def counts(key: str) -> str:
        return ", ".join(f"{medians[region][key]}/{n} ({region})" for region in REGIONS)

    return (
        f"**Figure {figure_number}. The overlap–volume dissociation in real data: dataset "
        "reference versus the published model in the 50-subject UCSF-PDGM evaluation cohort "
        "(Lundervold et al. 2026).** "
        f"**(A)** Subject UCSF-PDGM-{record['case']}, the cohort member whose whole-tumor (WT) "
        "Dice is closest to the cohort median, shown on the axial slice with the largest "
        f"reference WT area (z = {record['slice_z_mm']:.0f} mm, scanner coordinates; 1 mm "
        "isotropic; radiological orientation, patient right on image left). Dataset-reference "
        "labels are overlaid on the bias-corrected post-contrast T1-weighted image (T1c): "
        "necrotic tumor core, NCR (purple); enhancing tumor, ET (orange); peritumoral edema, "
        "ED (teal). "
        "**(B)** The same slice with reference (solid) and model (dashed) contours for WT "
        "(yellow; NCR + ED + ET) and ET (red). For this subject: WT "
        f"{change('WT')}; ET {change('ET')}. "
        "**(C)** Per-subject Dice against signed volume error (model − reference) for WT, tumor "
        f"core (TC; NCR + ET) and ET, n = {n}; open circles mark the subject in A–B. Medians: "
        f"{median('WT')}, {median('TC')}, {median('ET')}. The model volume was smaller than the "
        f"reference in {counts('n_model_smaller')} subjects, and |ΔV| ≥ 40% in "
        f"{counts('n_abs_volume_error_ge_40_percent')}. Points beyond ±100% are drawn at the "
        "panel edge with their values; such large relative errors arise from small reference "
        "compartments. Stars mark the two synthetic perturbations of Figure 1. Dotted lines show "
        "the optional RANO 2.0 volumetric thresholds (+40% progression, −65% partial response; "
        "Wen et al. 2023) for scale only: they apply to change between one patient's "
        "examinations, not to segmentation error. "
        "Recomputed Dice matched the companion's per-subject records (maximum absolute "
        f"difference {record['max_dice_difference_vs_companion']:.1e}); the median Dice values "
        f"{agreement} the published "
        + "/".join(f"{record['published_median_dice'][region]:.2f}" for region in REGIONS)
        + " (WT/TC/ET) at two decimals. Model label maps were produced by the companion study; "
        "no inference was rerun. Reference labels are the dataset's segmentations, not "
        "histological truth. Images and reference labels: UCSF-PDGM v5 (Calabrese et al. 2022; "
        "The Cancer Imaging Archive, doi:10.7937/tcia.bdgf-8v37), CC BY 4.0; changes: one slice "
        "cropped and overlaid with labels and contours."
    )
