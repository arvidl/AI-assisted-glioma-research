"""Prepared LUMIERE planes: geometry checks, local export and forward experiments.

Only explicitly supplied prepared data are read. No acquisition, segmentation,
registration, resampling or fitting is performed. Arrays and results stay local.
"""

import csv
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D

from glioma_ai.growth_model import simulate_density_2d
from glioma_ai.lumiere_slice import LABEL_SCHEME, VISITS, _require_label_scheme
from glioma_ai.provenance import environment_record, sha256

CORE_LABELS = (1, 4)
LABEL_NAMES = {1: "Necrotic / non-enhancing", 2: "Edema-associated", 4: "Enhancing"}
COLORS = {1: "#9b70ca", 2: "#3aafab", 4: "#f29b38"}


@dataclass
class SliceCase:
    """Six fixed-plane images/labels, with explicit geometry and provenance."""

    images: np.ndarray
    labels: np.ndarray
    metadata: dict

    @property
    def dx_mm(self) -> float:
        return float(self.metadata["spacing_mm"][0])

    @property
    def dy_mm(self) -> float:
        return float(self.metadata["spacing_mm"][1])

    def roi(self, visit: str, selected_labels: tuple[int, ...] = CORE_LABELS) -> np.ndarray:
        if not selected_labels or not set(selected_labels).issubset({1, 2, 4}):
            raise ValueError("Explicit ROI labels must be a nonempty subset of (1, 2, 4).")
        index = self.metadata["visit_names"].index(visit)
        return np.isin(self.labels[index], selected_labels)

    def areas(self) -> list[dict]:
        pixel_area = self.dx_mm * self.dy_mm
        return [
            {
                "visit": name,
                "nominal_week": int(name.split("-")[1]),
                **{
                    f"label_{label}_area_mm2": float((plane == label).sum() * pixel_area)
                    for label in (1, 2, 4)
                },
                "core_area_mm2": float(np.isin(plane, CORE_LABELS).sum() * pixel_area),
                "whole_union_area_mm2": float(np.isin(plane, (1, 2, 4)).sum() * pixel_area),
            }
            for name, plane in zip(self.metadata["visit_names"], self.labels, strict=True)
        ]


def _image_header(path: Path, *, label: bool = False) -> nib.Nifti1Image:
    image = nib.load(path)
    if len(image.shape) != 3:
        raise ValueError(f"Expected a 3D prepared image: {path.name}")
    units = image.header.get_xyzt_units()[0]
    if units != "mm" and not (label and units == "unknown"):
        raise ValueError(f"Unsupported spatial units {units!r}: {path.name}")
    qform, qcode = image.get_qform(coded=True)
    sform, scode = image.get_sform(coded=True)
    if not (qcode or scode) or not np.isfinite(image.affine).all():
        raise ValueError("A finite coded physical affine is required.")
    if qcode and scode and not np.allclose(qform, sform, atol=1e-3, rtol=0):
        raise ValueError("Coded qform and sform disagree.")
    axes = image.affine[:3, :3]
    spacing = np.linalg.norm(axes, axis=0)
    if not np.allclose(image.header.get_zooms()[:3], spacing, atol=1e-3, rtol=0):
        raise ValueError("Header spacing and physical affine disagree.")
    directions = axes / spacing
    if not np.allclose(directions.T @ directions, np.eye(3), atol=1e-6, rtol=0):
        raise ValueError("Sheared grids cannot be used by the orthogonal 2D model.")
    if not np.allclose(spacing, [1, 1, 1], atol=1e-3, rtol=0):
        raise ValueError("This prepared recipe requires 1-mm spacing; it will not resample.")
    if nib.aff2axcodes(image.affine) != ("R", "A", "S"):
        raise ValueError("This prepared recipe requires RAS axis directions.")
    return image


def prepare_slice_case(
    root: Path,
    *,
    axial_index: int | None = None,
    selection_visit: str = "week-045",
    selection_labels: tuple[int, ...] = CORE_LABELS,
) -> SliceCase:
    """Select a plane from the starting visit alone, then read that plane at all visits.

    The default is the first maximum-area core plane at week 045. Later labels
    do not influence slice choice. This remains retrospective case selection.
    Only the starting mask is loaded in 3D to count area by plane; CT1 data and
    the other label maps are extracted as 2D planes. All file hashes are retained.
    """
    root = Path(root)
    names = [visit["name"] for visit in VISITS]
    if selection_visit not in names:
        raise ValueError("The slice-selection visit must be in the prepared visit list.")
    if not selection_labels or not set(selection_labels).issubset({1, 2, 4}):
        raise ValueError("Slice-selection labels must be an explicit subset of (1, 2, 4).")
    headers, records, inputs = [], [], {}
    automatic_selection = axial_index is None
    for name in names:
        base = root / "derivatives" / f"tp-{name}"
        label_path = base / "seg_dl" / f"tp-{name}_seg_brats3_dl.nii.gz"
        record_path = label_path.with_name(f"tp-{name}_seg_brats3_dl.json")
        image_path = base / f"tp-{name}_CT1_to_ref.nii.gz"
        _require_label_scheme(record_path)
        records.append(json.loads(record_path.read_text()))
        image, label = _image_header(image_path), _image_header(label_path, label=True)
        if image.shape != label.shape or not np.allclose(
            image.affine, label.affine, atol=1e-3, rtol=0
        ):
            raise ValueError(f"Label and CT1 geometry differ at {name}; no alignment attempted.")
        if headers and (
            image.shape != headers[0][0].shape
            or not np.allclose(image.affine, headers[0][0].affine, atol=1e-3, rtol=0)
        ):
            raise ValueError("Visits are not on one prepared grid; no alignment attempted.")
        headers.append((image, label))
        for path in (image_path, label_path, record_path):
            inputs[str(path.relative_to(root))] = sha256(path)
        qc_path = base / "registration_qc.json"
        if qc_path.is_file():
            inputs[str(qc_path.relative_to(root))] = sha256(qc_path)
    if axial_index is None:
        starting_labels = np.asanyarray(headers[names.index(selection_visit)][1].dataobj)
        if not np.isin(starting_labels, (0, 1, 2, 4)).all():
            raise ValueError("Unknown labels in the starting volume; no relabeling attempted.")
        counts = np.isin(starting_labels, selection_labels).sum(axis=(0, 1))
        if counts.max() == 0:
            raise ValueError("Starting segmentation has no selected ROI; choose another case.")
        axial_index = int(np.argmax(counts))
    if isinstance(axial_index, bool) or not isinstance(axial_index, (int, np.integer)):
        raise ValueError("The slice index must be an integer.")
    if not 0 <= axial_index < headers[0][0].shape[2]:
        raise ValueError("The slice index is outside the prepared volume.")
    images, labels, windows = [], [], []
    for image, label in headers:
        intensity = np.asarray(image.dataobj[:, :, axial_index], dtype=float)
        plane = np.asarray(label.dataobj[:, :, axial_index], dtype=float)
        if not np.isfinite(intensity).all() or not np.isfinite(plane).all():
            raise ValueError("Nonfinite values in a selected image or label plane.")
        if not np.isin(plane, (0, 1, 2, 4)).all():
            raise ValueError("Unknown or noninteger labels; no relabeling attempted.")
        positive = intensity[intensity > 0]
        if not len(positive):
            raise ValueError("Selected CT1 plane contains no positive display values.")
        windows.append(np.percentile(positive, [1, 99]).tolist())
        images.append(intensity.astype(np.float32))
        labels.append(plane.astype(np.uint8))
    reference = headers[0][0]
    spacing = np.linalg.norm(reference.affine[:3, :3], axis=0)
    metadata = {
        "schema": "lumiere-fixed-plane-v1",
        "public_case": "LUMIERE-048",
        "source_doi": "10.1038/s41597-022-01881-7",
        "source_collection": "10.6084/m9.figshare.c.5904905.v1",
        "visit_names": names,
        "slice_index": int(axial_index),
        "selection_visit": selection_visit,
        "selection_labels": list(selection_labels),
        "slice_selection": (
            "starting-visit maximum ROI area; first tie; later data excluded"
            if automatic_selection
            else "explicit investigator-supplied plane index"
        ),
        "volume_shape": list(reference.shape),
        "affine": reference.affine.tolist(),
        "spacing_mm": spacing.tolist(),
        "axis_codes": "RAS",
        "coordinate_space": "prepared 1-mm reference grid, not native longitudinal anatomy",
        "label_scheme": LABEL_SCHEME,
        "label_source": "locally generated MONAI brats_mri_segmentation bundle 0.4.8",
        "expert_ground_truth": False,
        "label_header_units": [label.header.get_xyzt_units()[0] for _, label in headers],
        "label_units_evidence": "matched mm CT1 affine plus recorded bundle voxel spacing",
        "display_windows_p01_p99": windows,
        "display_only": "per-visit CT1 windowing, no quantitative intensity normalization",
        "time_basis": "nominal visit week labels; exact scan/treatment dates not modeled",
        "preparation": "registration/resampling and segmentation supplied upstream, not rerun",
        "upstream_device_records": [record.get("device") for record in records],
        "source_sha256": inputs,
        "review": "no new expert anatomical/segmentation review",
    }
    return SliceCase(np.stack(images), np.stack(labels), metadata)


def configured_case_inputs(repo_root: Path) -> dict:
    """Resolve explicit environment variables or an ignored local configuration.

    Never searches other repositories. Invalid explicit input is an error, not
    a reason to substitute synthetic data or another case.
    """
    prepared = os.environ.get("LUMIERE_P048_ROOT")
    bundle = os.environ.get("LUMIERE_P048_SLICE_BUNDLE")
    if prepared or bundle:
        config = {"prepared_root": prepared, "slice_bundle": bundle}
    else:
        path = Path(repo_root) / "local/lumiere-case.json"
        config = json.loads(path.read_text()) if path.is_file() else {}
    if config and bool(config.get("prepared_root")) == bool(config.get("slice_bundle")):
        raise ValueError("Configure exactly one prepared_root or slice_bundle.")
    return config


def load_configured_case(repo_root: Path) -> SliceCase | None:
    config = configured_case_inputs(repo_root)
    if not config:
        return None
    if config.get("slice_bundle"):
        return load_slice_case(Path(config["slice_bundle"]))
    return prepare_slice_case(Path(config["prepared_root"]), axial_index=config.get("axial_index"))


def export_slice_case(case: SliceCase, path: Path) -> Path:
    """Write a local, array-only slice bundle; never uploads or acquires anything."""
    path = Path(path)
    if path.suffix != ".npz":
        raise ValueError("Use an explicit .npz destination in ignored local storage.")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, images=case.images, labels=case.labels)
    path.with_suffix(".json").write_text(
        json.dumps(
            {
                **case.metadata,
                "bundle_sha256": sha256(path),
            },
            indent=2,
        )
        + "\n"
    )
    return path


def load_slice_case(path: Path) -> SliceCase:
    """Read a hash-checked paired .npz/.json bundle without object deserialization."""
    path = Path(path)
    record = json.loads(path.with_suffix(".json").read_text())
    if record.get("schema") != "lumiere-fixed-plane-v1" or sha256(path) != record["bundle_sha256"]:
        raise ValueError("Slice-bundle schema or SHA-256 mismatch.")
    with np.load(path, allow_pickle=False) as arrays:
        images, labels = arrays["images"].copy(), arrays["labels"].copy()
    if (
        images.ndim != 3
        or images.shape != labels.shape
        or min(images.shape[1:]) < 3
        or images.shape[0] != len(record["visit_names"])
        or not np.isfinite(images).all()
        or not np.isin(labels, (0, 1, 2, 4)).all()
        or record["label_scheme"] != LABEL_SCHEME
    ):
        raise ValueError("Invalid slice-bundle arrays or label meanings.")
    affine = np.asarray(record["affine"], dtype=float)
    spacing = np.asarray(record["spacing_mm"], dtype=float)
    if affine.shape != (4, 4) or spacing.shape != (3,) or not np.isfinite(affine).all():
        raise ValueError("Invalid bundle geometry.")
    if not np.allclose(spacing, [1, 1, 1], atol=1e-3, rtol=0) or not np.allclose(
        affine[:3, :3].T @ affine[:3, :3], np.diag(spacing**2), atol=1e-6, rtol=0
    ):
        raise ValueError("Bundle spacing or orthogonal geometry mismatch.")
    return SliceCase(images, labels, record)


def _extent(case: SliceCase) -> tuple[float, float, float, float]:
    # Intrinsic image-plane distances, not projected R/A world coordinates.
    nx, ny = case.labels.shape[1:]
    return (-case.dx_mm / 2, (nx - 0.5) * case.dx_mm, -case.dy_mm / 2, (ny - 0.5) * case.dy_mm)


def _format_plane(axis, case: SliceCase) -> None:
    axis.set_xlabel("Image axis 0 toward R (mm)")
    axis.set_ylabel("Image axis 1 toward A (mm)")
    axis.set_aspect("equal")


def _save(figure, output: Path, name: str) -> None:
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"{name}.{suffix}", dpi=170, bbox_inches="tight")
    plt.close(figure)


def write_observation_figures(case: SliceCase, output: Path) -> None:
    """Show all six visits without implying native-space volume or viable burden."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    extent = _extent(case)
    figure, axes = plt.subplots(2, 3, figsize=(12, 10), constrained_layout=True)
    for i, axis in enumerate(axes.flat):
        low, high = case.metadata["display_windows_p01_p99"][i]
        axis.imshow(
            case.images[i].T, origin="lower", extent=extent, cmap="gray", vmin=low, vmax=high
        )
        for label in (1, 2, 4):
            overlay = np.ma.masked_where(case.labels[i].T != label, case.labels[i].T)
            axis.imshow(
                overlay,
                origin="lower",
                extent=extent,
                cmap=ListedColormap([COLORS[label]]),
                alpha=0.65,
                vmin=0,
                vmax=4,
            )
        axis.set_title(case.metadata["visit_names"][i])
        _format_plane(axis, case)
    handles = [Line2D([0], [0], color=COLORS[k], lw=5, label=LABEL_NAMES[k]) for k in (1, 2, 4)]
    figure.legend(handles=handles, loc="outside lower center", ncols=3)
    figure.suptitle(
        f"LUMIERE-048: one prepared plane, index {case.metadata['slice_index']}\n"
        "Local AI labels; no new expert review; display window differs by visit"
    )
    _save(figure, output, "lumiere_observations")
    rows = case.areas()
    with (output / "lumiere_slice_areas.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    figure, axis = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    positions = np.arange(len(rows))
    bottom = np.zeros(len(rows))
    for label in (1, 2, 4):
        values = np.array([row[f"label_{label}_area_mm2"] for row in rows])
        axis.bar(positions, values, bottom=bottom, color=COLORS[label], label=LABEL_NAMES[label])
        bottom += values
    axis.set_xticks(positions, [row["visit"] for row in rows], rotation=15)
    axis.set_ylabel("Automated compartment area on this plane (mm²)")
    axis.legend(loc="upper left")
    axis.set_title("Fixed-plane observations: no interpolation across surgery or treatment")
    _save(figure, output, "lumiere_areas")


def compare_masks(prediction: np.ndarray, observation: np.ndarray, pixel_area: float) -> dict:
    """Descriptive automated-label agreement; not accuracy against expert truth."""
    p, y = np.asarray(prediction, dtype=bool), np.asarray(observation, dtype=bool)
    if p.shape != y.shape or p.ndim != 2:
        raise ValueError("Comparison masks must share one 2D plane.")
    denominator = int(p.sum() + y.sum())
    return {
        "dice": float(2 * np.count_nonzero(p & y) / denominator) if denominator else 1.0,
        "predicted_area_mm2": float(p.sum() * pixel_area),
        "observed_automated_area_mm2": float(y.sum() * pixel_area),
        "missed_label_area_mm2": float(np.count_nonzero(y & ~p) * pixel_area),
        "additional_model_area_mm2": float(np.count_nonzero(p & ~y) * pixel_area),
    }


def run_case_experiment(
    case: SliceCase,
    output: Path,
    *,
    initial_visit: str = "week-045",
    comparison_visit: str = "week-049",
    selected_labels: tuple[int, ...] = CORE_LABELS,
    initial_occupancy: float = 0.65,
    diffusivity_mm2_per_day: float = 0.35,
    rho_per_day: float = 0.035,
    dt_days: float = 0.2,
    threshold: float = 0.5,
) -> dict:
    """Retrospective forward comparison, controls, sensitivity and local provenance.

    The ROI is a structural seed, including necrotic/non-enhancing label 1 by
    default. Occupancy and display thresholds are unmeasured assumptions. No
    treatment term or through-plane flux is modeled. The sensitivity grid does
    not select or report a best patient coefficient.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if not np.isfinite(initial_occupancy) or not 0 < threshold < initial_occupancy <= 1:
        raise ValueError("Require 0 < display threshold < initial occupancy <= 1.")
    start_week, end_week = (int(name.split("-")[1]) for name in (initial_visit, comparison_visit))
    duration = 7 * (end_week - start_week)
    if duration <= 0:
        raise ValueError("Choose a strictly later nominal week, without crossing resection.")
    if initial_visit.startswith("week-000"):
        raise ValueError("This growth-only example must not span the perioperative interval.")
    initial_mask = case.roi(initial_visit, selected_labels)
    observed = case.roi(comparison_visit, selected_labels)
    if not initial_mask.any():
        raise ValueError("The starting plane contains no selected ROI.")
    initial = initial_occupancy * initial_mask
    times = np.linspace(0, duration, 15)
    kwargs = {"dx_mm": case.dx_mm, "dy_mm": case.dy_mm, "dt_days": dt_days}
    controls = {
        "No change": (0.0, 0.0),
        "Diffusion only": (diffusivity_mm2_per_day, 0.0),
        "Reaction only": (0.0, rho_per_day),
        "Reaction + diffusion": (diffusivity_mm2_per_day, rho_per_day),
    }
    runs = {
        name: simulate_density_2d(initial, d, r, times, **kwargs)
        for name, (d, r) in controls.items()
    }
    model = runs["Reaction + diffusion"]
    pixel_area = case.dx_mm * case.dy_mm
    comparisons = {
        name: compare_masks(run.density[-1] >= threshold, observed, pixel_area)
        for name, run in runs.items()
    }
    extent = _extent(case)
    coords = (np.arange(initial.shape[0]) * case.dx_mm, np.arange(initial.shape[1]) * case.dy_mm)
    # The crop affects display only; the full prepared plane is the solver domain.
    bbox = np.argwhere(initial_mask | observed)
    limits = (
        (
            max(0, bbox[:, 0].min() - 25) * case.dx_mm,
            min(initial.shape[0] - 1, bbox[:, 0].max() + 25) * case.dx_mm,
        ),
        (
            max(0, bbox[:, 1].min() - 25) * case.dy_mm,
            min(initial.shape[1] - 1, bbox[:, 1].max() + 25) * case.dy_mm,
        ),
    )
    figure, axes = plt.subplots(2, 3, figsize=(13.5, 8.5), constrained_layout=True)
    for axis, k in zip(axes[0], (0, 7, 14), strict=True):
        panel = axis.imshow(
            model.density[k].T, extent=extent, origin="lower", cmap="magma", vmin=0, vmax=1
        )
        axis.set_title(f"Model t = {times[k]:g} days")
    figure.colorbar(
        panel, ax=list(axes[0]), label="Prescribed normalized density proxy c", shrink=0.75
    )
    comparison_index = case.metadata["visit_names"].index(comparison_visit)
    low, high = case.metadata["display_windows_p01_p99"][comparison_index]
    axes[1, 0].imshow(
        case.images[comparison_index].T,
        extent=extent,
        origin="lower",
        cmap="gray",
        vmin=low,
        vmax=high,
    )
    for mask, color in ((observed, "#48dbbf"), (model.density[-1] >= threshold, "#ffbd57")):
        if mask.any() and not mask.all():
            axes[1, 0].contour(*coords, mask.T, levels=[0.5], colors=[color], linewidths=1.5)
    axes[1, 0].set_title("Later CT1: label (teal), model (orange)")
    difference = np.zeros_like(initial, dtype=int)
    prediction = model.density[-1] >= threshold
    difference[observed & prediction] = 1
    difference[observed & ~prediction] = 2
    difference[prediction & ~observed] = 3
    axes[1, 1].imshow(
        difference.T,
        extent=extent,
        origin="lower",
        vmin=0,
        vmax=3,
        cmap=ListedColormap(["#ededed", "#426b72", "#3bc6a8", "#ed9b39"]),
    )
    axes[1, 1].set_title("Dark: overlap; teal: missed; orange: additional")
    axes[1, 2].axis("off")
    text = (
        f"Prescribed D = {diffusivity_mm2_per_day:g} mm²/day\n"
        f"Prescribed ρ = {rho_per_day:g} /day\n"
        f"Initial occupancy = {initial_occupancy:g}; threshold = {threshold:g}\n"
        f"Nominal interval = {duration:g} days\n\n"
        "ROI labels: " + ", ".join(map(str, selected_labels)) + "\n"
        "Agreement is with automated labels.\n"
        "No coefficient fit, expert truth or treatment term.\n"
        "No flux at the full-plane outer rectangle.\n"
        "Shown crop is for display only."
    )
    axes[1, 2].text(0, 0.92, text, va="top", fontsize=11, linespacing=1.6)
    for axis in list(axes[0]) + list(axes[1, :2]):
        _format_plane(axis, case)
        axis.set_xlim(*limits[0])
        axis.set_ylim(*limits[1])
    figure.suptitle(
        "LUMIERE-048: observed anatomy seeds a conditional 2D model\n"
        "Retrospective illustration; modeled density is not measured cell burden"
    )
    _save(figure, output, "lumiere_model")
    figure, axes = plt.subplots(1, 3, figsize=(13, 4.6), constrained_layout=True)
    for name, run in runs.items():
        axes[0].plot(times, run.integral_mm2, label=name)
        axes[1].plot(times, run.areas_mm2(threshold), label=name)
    axes[0].set_ylabel("Integrated density proxy M (mm²)")
    axes[1].set_ylabel(f"Model area at c ≥ {threshold:g} (mm²)")
    axes[1].scatter(
        [duration],
        [observed.sum() * pixel_area],
        color="black",
        marker="x",
        s=75,
        label="Later automated core area",
    )
    for axis in axes[:2]:
        axis.set_xlabel("Model elapsed time (days)")
        axis.legend(fontsize=8)
    levels = np.linspace(0.1, 0.6, 26)
    axes[2].plot(levels, [(model.density[-1] >= level).sum() * pixel_area for level in levels])
    axes[2].axhline(observed.sum() * pixel_area, color="black", linestyle="--")
    axes[2].set_xlabel("Uncalibrated display threshold")
    axes[2].set_ylabel("Final model area (mm²)")
    figure.suptitle("Controls and observation assumptions: increasing M need not increase area")
    _save(figure, output, "lumiere_controls")
    d_values, rho_values, thresholds = [0.1, 0.35, 0.7, 1.0], [0, 0.02, 0.035, 0.07], [0.3, 0.5]
    landscape = np.empty((len(thresholds), len(rho_values), len(d_values)))
    sensitivity_rows = []
    for j, rho in enumerate(rho_values):
        for i, d in enumerate(d_values):
            run = simulate_density_2d(initial, d, rho, [0, duration], **kwargs)
            for k, level in enumerate(thresholds):
                metrics = compare_masks(run.density[-1] >= level, observed, pixel_area)
                landscape[k, j, i] = metrics["dice"]
                sensitivity_rows.append(
                    {"D_mm2_per_day": d, "rho_per_day": rho, "threshold": level, **metrics}
                )
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.8), constrained_layout=True)
    for k, axis in enumerate(axes):
        panel = axis.imshow(landscape[k], origin="lower", vmin=0, vmax=1, cmap="viridis")
        axis.set_xticks(range(len(d_values)), d_values)
        axis.set_yticks(range(len(rho_values)), rho_values)
        axis.set_xlabel("Prescribed D (mm²/day)")
        axis.set_ylabel("Prescribed ρ (/day)")
        axis.set_title(f"Display threshold {thresholds[k]:g}")
        for j in range(len(rho_values)):
            for i in range(len(d_values)):
                axis.text(
                    i, j, f"{landscape[k, j, i]:.2f}", ha="center", va="center", color="white"
                )
    figure.colorbar(panel, ax=list(axes), label="Dice with later automated core label", shrink=0.8)
    figure.suptitle("Retrospective sensitivity: no best patient parameter is selected")
    _save(figure, output, "lumiere_sensitivity")
    assumptions = []
    for occupancy in (0.55, 0.65, 1.0):
        for elapsed in (21, 28, 35):
            run = simulate_density_2d(
                occupancy * initial_mask,
                diffusivity_mm2_per_day,
                rho_per_day,
                [0, elapsed],
                **kwargs,
            )
            assumptions.append(
                {
                    "initial_occupancy": occupancy,
                    "assumed_days": elapsed,
                    **compare_masks(run.density[-1] >= threshold, observed, pixel_area),
                }
            )
    refined = simulate_density_2d(
        initial, diffusivity_mm2_per_day, rho_per_day, times, **{**kwargs, "dt_days": dt_days / 2}
    )
    edge = np.concatenate(
        (
            model.density[-1, 0],
            model.density[-1, -1],
            model.density[-1, :, 0],
            model.density[-1, :, -1],
        )
    )
    result = {
        "evidence_type": "real automated-label observations + prescribed forward model",
        "case": case.metadata,
        "observations": case.areas(),
        "initial_visit": initial_visit,
        "comparison_visit": comparison_visit,
        "parameters": {
            "D_mm2_per_day": diffusivity_mm2_per_day,
            "rho_per_day": rho_per_day,
            "initial_occupancy": initial_occupancy,
            "selected_labels": list(selected_labels),
            "threshold": threshold,
            "nominal_elapsed_days": duration,
            "dt_days_max": dt_days,
        },
        "solver": "exact half reaction / conservative Euler diffusion / exact half reaction",
        "domain": "full prepared 2D rectangle; no anatomical brain boundary or through-plane flux",
        "comparisons": comparisons,
        "coefficient_sensitivity": sensitivity_rows,
        "initialization_and_timing_sensitivity": assumptions,
        "numerics": {
            "n_steps": model.n_steps,
            "largest_step_days": model.largest_step_days,
            "diffusion_step_bound_days": model.step_limit_days,
            "max_discrete_balance_residual_mm2": model.max_balance_residual_mm2,
            "step_halving_density_rms": float(
                np.sqrt(np.mean((model.density[-1] - refined.density[-1]) ** 2))
            ),
            "max_final_outer_boundary_density": float(edge.max()),
            "density_min": float(model.density.min()),
            "density_max": float(model.density.max()),
        },
        "inference": "no patient coefficient estimation or recurrence prediction",
        "limitations": [
            "no treatment history",
            "no tissue-dependent migration or brain boundary",
            "no viable-cell or density measurements",
            "single case/plane",
            "labels and registration not independently reviewed",
            "no held-out evaluation",
        ],
        "ai_roles": {
            "upstream": case.metadata["label_source"],
            "research_assistant": "implementation, math explanation and numerical checks",
            "numerical_solver": "deterministic classical model, not an AI prediction",
            "benefit_evaluation": "not performed",
        },
    }
    (output / "lumiere_dynamics.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    np.savez_compressed(
        output / "lumiere_model_snapshots.npz",
        days=times,
        density=model.density,
        initial_mask=initial_mask,
        later_automated_mask=observed,
    )
    with (output / "lumiere_sensitivity.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=list(sensitivity_rows[0]))
        writer.writeheader()
        writer.writerows(sensitivity_rows)
    with (output / "lumiere_model_traces.tsv").open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "model",
                "elapsed_days",
                "integral_proxy_mm2",
                "area_threshold_mm2",
                "reaction_gain_mm2",
            ]
        )
        for name, run in runs.items():
            writer.writerows(
                zip(
                    [name] * len(times),
                    times,
                    run.integral_mm2,
                    run.areas_mm2(threshold),
                    run.reaction_gain_mm2,
                    strict=True,
                )
            )
    assets = sorted(p for p in output.glob("lumiere_*.*") if p.name != "lumiere_run.json")
    (output / "lumiere_run.json").write_text(
        json.dumps(
            {
                **environment_record(),
                "input_sha256": case.metadata["source_sha256"],
                "parameters": result["parameters"],
                "output_sha256": {p.name: sha256(p) for p in assets},
            },
            indent=2,
        )
        + "\n"
    )
    return result


def write_case_paper_assets(result: dict, output: Path, paper_dir: Path) -> None:
    """Copy local figures and generate numbers; no patient values enter source text."""
    paper_dir = Path(paper_dir)
    paper_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "lumiere_observations",
        "lumiere_areas",
        "lumiere_model",
        "lumiere_controls",
        "lumiere_sensitivity",
    ):
        shutil.copy2(Path(output) / f"{name}.pdf", paper_dir / f"{name}.pdf")
    final = result["comparisons"]["Reaction + diffusion"]
    macros = {
        "LumiereGrowthSlice": str(result["case"]["slice_index"]),
        "LumiereGrowthInitialArea": (
            f"{result['comparisons']['No change']['predicted_area_mm2']:.1f}"
        ),
        "LumiereGrowthLaterArea": f"{final['observed_automated_area_mm2']:.1f}",
        "LumiereGrowthModelArea": f"{final['predicted_area_mm2']:.1f}",
        "LumiereGrowthDice": f"{final['dice']:.3f}",
        "LumiereGrowthNoChangeDice": f"{result['comparisons']['No change']['dice']:.3f}",
        "LumiereGrowthBalanceError": (
            f"{result['numerics']['max_discrete_balance_residual_mm2']:.2e}"
        ),
    }
    (paper_dir / "lumiere_growth_numbers.tex").write_text(
        "% Generated locally from prepared public case; automated-label observations.\n"
        + "".join("\\newcommand{\\" + k + "}{" + v + "}\n" for k, v in macros.items())
    )
