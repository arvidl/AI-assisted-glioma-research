"""One axial slice of LUMIERE Patient-048 and a prescribed 2D growth step.

The volumes are read from a local extract. This module does not register,
resample, or relabel them. The explicit step uses a prescribed diffusivity
and proliferation. It does not estimate those fields and does not cross the
resection between day 0 and day 3.
"""

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from numpy.typing import NDArray

from glioma_ai.growth import integrate_fisher_2d

WHOLE_TUMOR_LABELS = (1, 2, 4)
LABEL_SCHEME = {
    "background": 0,
    "necrosis_or_non_enhancing": 1,
    "edema": 2,
    "enhancing_tumor": 4,
}
# Week-derived days. From week-013 onward, day = week * 7, so the archive's
# week binning leaves about three days of uncertainty. Day 0 and day 3 are the
# preoperative and immediate postoperative scans: the released tables give only
# week 0 for both, and day 3 is the label in Suter et al. (2022), Fig. 2, whose
# unnamed example patient has exactly Patient-048's visits and ratings.
VISITS = (
    {"name": "week-000-1", "day": 0, "rating": "Pre-Op", "drawn": True, "role": "observation"},
    {"name": "week-000-2", "day": 3, "rating": "Post-Op", "drawn": True, "role": "observation"},
    {"name": "week-013", "day": 91, "rating": "SD", "drawn": False, "role": "slice-selection"},
    {"name": "week-023", "day": 161, "rating": "CR", "drawn": False, "role": "slice-selection"},
    {"name": "week-045", "day": 315, "rating": "PD", "drawn": True, "role": "initial"},
    {"name": "week-049", "day": 343, "rating": "PD", "drawn": True, "role": "comparison"},
)
DIFFUSIVITY_MM2_PER_DAY = 0.5
PROLIFERATION_PER_DAY = 0.02
# Same proliferation and time step, with diffusivity doubled. The explicit
# stability limit at 1 mm spacing is dt <= 1/(4D), so D = 1 mm^2/day is the
# largest doubling that this time step still accepts. It is not a fit.
ALTERNATIVE_DIFFUSIVITY_MM2_PER_DAY = 1.0
ALTERNATIVE_PROLIFERATION_PER_DAY = 0.02
TIME_STEP_DAYS = 0.25
VISIBLE_THRESHOLD = 0.5
CROP_MARGIN_VOXELS = 16


def lumiere_p048_root(repo_root: Path | None = None) -> Path | None:
    """Return the local Patient-048 extract when its reference label map is present.

    LUMIERE_P048_ROOT takes precedence. Only when repo_root is given is the
    prepared_root of its ignored local/lumiere-case.json also consulted.
    """
    override = os.environ.get("LUMIERE_P048_ROOT")
    if not override and repo_root is not None:
        config = Path(repo_root) / "local/lumiere-case.json"
        if config.is_file():
            override = json.loads(config.read_text()).get("prepared_root")
    if not override:
        return None
    root = Path(override)
    marker = Path("derivatives/tp-week-000-1/seg_dl/tp-week-000-1_seg_brats3_dl.nii.gz")
    return root if (root / marker).is_file() else None


def select_axial_index(label_maps: list[NDArray[np.generic]]) -> int:
    """Pick the superior-axis index that cuts tumor at every visit.

    The score of an index is the smallest whole-tumor voxel count across the
    supplied maps. The first maximum wins. Axis 2 is superior only for a RAS
    volume; callers check that orientation before using the index as anatomy.
    """
    if len(label_maps) < 2:
        raise ValueError("Select a slice from at least two label maps.")
    shape = label_maps[0].shape
    if len(shape) != 3 or any(map_.shape != shape for map_ in label_maps):
        raise ValueError("Label maps must be 3D and share a shape.")
    counts = np.stack([np.isin(map_, WHOLE_TUMOR_LABELS).sum(axis=(0, 1)) for map_ in label_maps])
    present = np.all(counts > 0, axis=0)
    if not present.any():
        raise ValueError("No axial index intersects the whole-tumor label at every visit.")
    score = np.where(present, counts.min(axis=0), -1)
    return int(np.argmax(score))


def slice_specification() -> dict:
    """Record the 2D equation, the prescribed inputs, and the tasks not done."""
    return {
        "schema": "spatiotemporal-slice-v1",
        "state": "normalized density on one axial slice",
        "equation": "dc/dt = div(D grad c) + rho c (1-c)",
        "coordinate_unit": "mm",
        "boundary": "no flux at the edge of the slice",
        "fields_prescribed": ["diffusivity", "proliferation", "initial indicator"],
        "solver": "explicit finite difference",
        "stability_rule": "dt <= 1 / (2 max(D) (dx^{-2} + dy^{-2}))",
        "inverse_estimation": "not_performed",
        "recurrence_prediction": "not_performed",
        "patient": "LUMIERE-048",
        "interval": "week-045 to week-049",
        "crosses_resection": False,
    }


def _load_image(path: Path, *, require_mm: bool) -> tuple[np.ndarray, np.ndarray, str]:
    image = nib.load(str(path))
    units = image.header.get_xyzt_units()[0]
    if require_mm and units != "mm":
        raise ValueError(f"{path.name} is not in millimetre units.")
    if units not in {"mm", "unknown"}:
        raise ValueError(f"{path.name} has spatial units {units}, which this slice does not use.")
    qform, qcode = image.get_qform(coded=True)
    sform, scode = image.get_sform(coded=True)
    if not qcode and not scode:
        raise ValueError(f"{path.name} has no coded spatial transform.")
    if qcode and scode and not np.allclose(qform, sform, rtol=0, atol=1e-3):
        raise ValueError(f"{path.name} has disagreeing qform and sform.")
    affine = np.asarray(image.affine, dtype=float)
    zooms = tuple(float(zoom) for zoom in image.header.get_zooms()[:3])
    if not np.allclose(zooms, (1.0, 1.0, 1.0), rtol=0, atol=1e-3):
        raise ValueError(f"{path.name} is not on a 1 mm grid.")
    if "".join(nib.aff2axcodes(affine)) != "RAS":
        raise ValueError(f"{path.name} is not RAS; the superior axis is not established.")
    return np.asanyarray(image.dataobj), affine, units


def _require_label_scheme(path: Path) -> None:
    record = json.loads(path.read_text())
    if record.get("label_scheme") != LABEL_SCHEME:
        raise ValueError(f"{path.name} does not use the expected BraTS label scheme.")
    if record.get("bundle_version") != "0.4.8" or record.get("backend") != "monai_bundle":
        raise ValueError(f"{path.name} is not the expected MONAI bundle record.")
    if record.get("voxel_spacing_mm") != [1.0, 1.0, 1.0]:
        raise ValueError(f"{path.name} does not record 1 mm spacing.")


def _crop_box(masks: list[np.ndarray], margin: int) -> tuple[slice, slice]:
    selected = np.zeros(masks[0].shape, dtype=bool)
    for mask in masks:
        selected |= mask
    rows = np.where(selected.any(axis=1))[0]
    cols = np.where(selected.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        raise ValueError("The selected slice has no whole-tumor voxels to crop.")
    row_0 = max(int(rows[0]) - margin, 0)
    row_1 = min(int(rows[-1]) + margin + 1, selected.shape[0])
    col_0 = max(int(cols[0]) - margin, 0)
    col_1 = min(int(cols[-1]) + margin + 1, selected.shape[1])
    return slice(row_0, row_1), slice(col_0, col_1)


def component_coverage(reference: np.ndarray, prediction: np.ndarray) -> list[tuple[int, int]]:
    """Area and overlap of each 4-connected component of ``reference``.

    Overlap counts reference voxels that are also set in ``prediction``. The
    arrays must already share a grid. This does not relabel the source map.
    """
    if reference.shape != prediction.shape or reference.ndim != 2:
        raise ValueError("Component coverage requires aligned 2D masks.")
    visited = np.zeros(reference.shape, dtype=bool)
    height, width = reference.shape
    coverage = []
    for start_y, start_x in np.argwhere(reference):
        start = (int(start_y), int(start_x))
        if visited[start]:
            continue
        stack = [start]
        visited[start] = True
        area, overlap = 0, 0
        while stack:
            y, x = stack.pop()
            area += 1
            overlap += int(prediction[y, x])
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if (
                    0 <= ny < height
                    and 0 <= nx < width
                    and reference[ny, nx]
                    and not visited[ny, nx]
                ):
                    visited[ny, nx] = True
                    stack.append((ny, nx))
        coverage.append((area, overlap))
    return sorted(coverage, reverse=True)


def compartment_areas_mm2(label_plane: np.ndarray) -> dict[str, int]:
    """Count BraTS compartments on one axial plane. Each voxel is 1 mm².

    The counts are the stored labels. They are not an expert re-contour and
    not a RANO measurement.
    """
    if label_plane.ndim != 2:
        raise ValueError("Compartment areas require one axial plane.")
    plane = np.asarray(label_plane)
    if not np.isfinite(plane).all() or np.any(plane != np.floor(plane)):
        raise ValueError("Compartment areas require an integer label plane.")
    return {
        "necrosis_or_non_enhancing": int(np.count_nonzero(plane == 1)),
        "edema": int(np.count_nonzero(plane == 2)),
        "enhancing_tumor": int(np.count_nonzero(plane == 4)),
    }


def largest_uncovered_mask(reference: np.ndarray, prediction: np.ndarray) -> np.ndarray:
    """Largest 4-connected component of ``reference`` that ``prediction`` misses.

    A component is missed when no reference voxel in it is set in ``prediction``.
    The result is empty when every component overlaps ``prediction``.
    """
    if reference.shape != prediction.shape or reference.ndim != 2:
        raise ValueError("An uncovered component requires aligned 2D masks.")
    visited = np.zeros(reference.shape, dtype=bool)
    height, width = reference.shape
    best_area = 0
    best: list[tuple[int, int]] = []
    for start_y, start_x in np.argwhere(reference):
        start = (int(start_y), int(start_x))
        if visited[start]:
            continue
        stack = [start]
        visited[start] = True
        voxels: list[tuple[int, int]] = []
        overlap = 0
        while stack:
            y, x = stack.pop()
            voxels.append((y, x))
            overlap += int(prediction[y, x])
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if (
                    0 <= ny < height
                    and 0 <= nx < width
                    and reference[ny, nx]
                    and not visited[ny, nx]
                ):
                    visited[ny, nx] = True
                    stack.append((ny, nx))
        if overlap == 0 and len(voxels) > best_area:
            best_area = len(voxels)
            best = voxels
    mask = np.zeros(reference.shape, dtype=bool)
    for y, x in best:
        mask[y, x] = True
    return mask


def min_distance_mm(source: np.ndarray, target: np.ndarray) -> float:
    """Minimum Euclidean distance, in 1 mm voxels, from ``source`` to ``target``."""
    if source.shape != target.shape or source.ndim != 2:
        raise ValueError("Distance requires aligned 2D masks.")
    source_points = np.argwhere(source)
    target_points = np.argwhere(target)
    if source_points.size == 0 or target_points.size == 0:
        raise ValueError("Distance requires nonempty masks.")
    nearest = np.empty(source_points.shape[0], dtype=float)
    for start in range(0, source_points.shape[0], 256):
        chunk = source_points[start : start + 256, None, :].astype(float)
        delta = chunk - target_points[None, :, :]
        nearest[start : start + chunk.shape[0]] = np.sqrt((delta * delta).sum(axis=2).min(axis=1))
    return float(nearest.min())


def _dice(prediction: np.ndarray, reference: np.ndarray) -> float:
    if prediction.shape != reference.shape or prediction.ndim != 2:
        raise ValueError("Dice inputs must be 2D and aligned.")
    denominator = int(prediction.sum()) + int(reference.sum())
    if denominator == 0:
        return 1.0
    return float(2 * np.count_nonzero(prediction & reference) / denominator)


def _display_limits(image: np.ndarray) -> tuple[float, float]:
    positive = image[image > 0]
    if positive.size == 0:
        raise ValueError("The slice has no positive post-contrast intensities to display.")
    low, high = np.percentile(positive, (1, 99))
    if high <= low:
        raise ValueError("The display window is degenerate.")
    return float(low), float(high)


def illustrate_patient048(root: Path) -> dict:
    """Load the shared grid, choose one axial index, and advance a prescribed step.

    Post-contrast T1 and the MONAI BraTS label map are read at each visit.
    Affines must match the preoperative grid. The solved interval is day 315
    to day 343. Both of those visits are rated progressive disease.
    """
    root = Path(root)
    reference_affine = None
    labels = []
    images = {}
    label_unit_codes = set()
    for visit in VISITS:
        name = visit["name"]
        folder = root / "derivatives" / f"tp-{name}"
        _require_label_scheme(folder / "seg_dl" / f"tp-{name}_seg_brats3_dl.json")
        label_map, label_affine, label_units = _load_image(
            folder / "seg_dl" / f"tp-{name}_seg_brats3_dl.nii.gz", require_mm=False
        )
        ct1, ct1_affine, _ct1_units = _load_image(
            folder / f"tp-{name}_CT1_to_ref.nii.gz", require_mm=True
        )
        if label_map.shape != ct1.shape or not np.allclose(label_affine, ct1_affine, atol=1e-3):
            raise ValueError(f"{name} label map and post-contrast T1 do not share a grid.")
        label_unit_codes.add(label_units)
        if reference_affine is None:
            reference_affine = ct1_affine
        elif not np.allclose(ct1_affine, reference_affine, atol=1e-3):
            raise ValueError(f"{name} is not on the preoperative reference grid.")
        if not np.isfinite(ct1).all():
            raise ValueError(f"{name} post-contrast T1 contains a non-finite value.")
        observed = np.unique(label_map)
        if not np.isfinite(label_map).all() or np.any(label_map != np.floor(label_map)):
            raise ValueError(f"{name} label map is not an integer field.")
        unknown = sorted(set(int(value) for value in observed) - set(LABEL_SCHEME.values()))
        if unknown:
            raise ValueError(f"{name} contains labels outside the stated scheme: {unknown}.")
        labels.append(label_map.astype(np.int16, copy=False))
        if visit["drawn"] or visit["role"] in {"initial", "comparison"}:
            images[name] = np.asarray(ct1, dtype=np.float32)
    index = select_axial_index(labels)
    label_planes = {
        visit["name"]: label_map[:, :, index]
        for visit, label_map in zip(VISITS, labels, strict=True)
    }
    planes = {name: np.isin(plane, WHOLE_TUMOR_LABELS) for name, plane in label_planes.items()}
    initial_name = next(visit["name"] for visit in VISITS if visit["role"] == "initial")
    later_name = next(visit["name"] for visit in VISITS if visit["role"] == "comparison")
    elapsed = next(visit["day"] for visit in VISITS if visit["name"] == later_name) - next(
        visit["day"] for visit in VISITS if visit["name"] == initial_name
    )
    if elapsed <= 0 or (elapsed / TIME_STEP_DAYS) != int(elapsed / TIME_STEP_DAYS):
        raise ValueError("The solved interval is not an integer number of time steps.")
    density = integrate_fisher_2d(
        planes[initial_name].astype(float),
        DIFFUSIVITY_MM2_PER_DAY,
        PROLIFERATION_PER_DAY,
        1.0,
        1.0,
        TIME_STEP_DAYS,
        int(elapsed / TIME_STEP_DAYS),
    )
    simulated = density >= VISIBLE_THRESHOLD
    alternative = integrate_fisher_2d(
        planes[initial_name].astype(float),
        ALTERNATIVE_DIFFUSIVITY_MM2_PER_DAY,
        ALTERNATIVE_PROLIFERATION_PER_DAY,
        1.0,
        1.0,
        TIME_STEP_DAYS,
        int(elapsed / TIME_STEP_DAYS),
    )
    alternative_mask = alternative >= VISIBLE_THRESHOLD
    uncovered_mask = largest_uncovered_mask(planes[later_name], simulated)
    uncovered_labels = compartment_areas_mm2(np.where(uncovered_mask, label_planes[later_name], 0))
    if int(uncovered_mask.sum()) != sum(uncovered_labels.values()):
        raise ValueError("The uncovered component is not accounted for by the stated labels.")
    initial_centroid = np.argwhere(planes[initial_name]).mean(axis=0)
    missed_centroid = np.argwhere(uncovered_mask).mean(axis=0)
    # Axis 0 increases toward the patient's right and axis 1 increases anteriorly.
    offset_right_mm = float(missed_centroid[0] - initial_centroid[0])
    offset_anterior_mm = float(missed_centroid[1] - initial_centroid[1])
    drawn = [visit for visit in VISITS if visit["drawn"]]
    crop = _crop_box([planes[visit["name"]] for visit in drawn], CROP_MARGIN_VOXELS)
    areas = {visit["name"]: int(planes[visit["name"]].sum()) for visit in VISITS}
    return {
        "specification": slice_specification(),
        "patient": "LUMIERE-048",
        "source": "Suter et al., Scientific Data 2022; Figshare 10.6084/m9.figshare.c.5904905.v1",
        "coordinate_space": (
            "1 mm RAS grid of the preoperative T1. Later visits were already "
            "rigidly resampled onto that grid; this function checks the affines "
            "and does not estimate a transform. The label-map header does not "
            "code spatial units; millimetres come from the matched post-contrast "
            "T1 header and from the segmentation record's 1 mm spacing."
        ),
        "image": "post-contrast T1",
        "mask": (
            "MONAI bundle brats_mri_segmentation 0.4.8 on the same grid. "
            "Labels 1, 2, and 4 are necrosis or non-enhancing tumor, edema, "
            "and enhancing tumor. The whole-tumor indicator is their union."
        ),
        "label_header_units": sorted(label_unit_codes),
        "axial_index": index,
        "axial_axis": "superior, axis 2 of the stored RAS volume",
        "crop_slices": (crop[0].start, crop[0].stop, crop[1].start, crop[1].stop),
        "visits": [
            {
                "name": visit["name"],
                "day": visit["day"],
                "rating": visit["rating"],
                "drawn": visit["drawn"],
                "role": visit["role"],
                "whole_tumor_area_mm2": areas[visit["name"]],
            }
            for visit in VISITS
        ],
        "solved_interval_days": elapsed,
        "parameters": {
            "diffusivity_mm2_per_day": DIFFUSIVITY_MM2_PER_DAY,
            "proliferation_per_day": PROLIFERATION_PER_DAY,
            "dt_days": TIME_STEP_DAYS,
            "n_steps": int(elapsed / TIME_STEP_DAYS),
            "visible_threshold": VISIBLE_THRESHOLD,
            "dx_mm": 1.0,
            "dy_mm": 1.0,
        },
        "simulated_area_mm2": int(simulated.sum()),
        "comparison_dice": _dice(simulated, planes[later_name]),
        "baseline_dice": _dice(planes[initial_name], planes[later_name]),
        "alternative": {
            "diffusivity_mm2_per_day": ALTERNATIVE_DIFFUSIVITY_MM2_PER_DAY,
            "proliferation_per_day": ALTERNATIVE_PROLIFERATION_PER_DAY,
            "simulated_area_mm2": int(alternative_mask.sum()),
            "comparison_dice": _dice(alternative_mask, planes[later_name]),
            "role": (
                "sensitivity case with doubled diffusivity, the same proliferation, "
                "and the same time step; not a fitted pair"
            ),
        },
        "compartments_mm2": {
            initial_name: compartment_areas_mm2(label_planes[initial_name]),
            later_name: compartment_areas_mm2(label_planes[later_name]),
        },
        "largest_uncovered_component_mm2": int(uncovered_mask.sum()),
        "largest_uncovered_component": {
            "area_mm2": int(uncovered_mask.sum()),
            **uncovered_labels,
            "min_distance_to_day315_whole_tumor_mm": min_distance_mm(
                uncovered_mask, planes[initial_name]
            ),
            "min_distance_to_prescribed_contour_mm": min_distance_mm(uncovered_mask, simulated),
            "offset_from_day315_centroid_right_mm": offset_right_mm,
            "offset_from_day315_centroid_anterior_mm": offset_anterior_mm,
            "expert_recontour": "not_performed",
            "registration_reestimated": "not_performed",
        },
        "density_min": float(density.min()),
        "density_max": float(density.max()),
        "_planes": planes,
        "_images": images,
        "_density": density,
        "_crop": crop,
        "_uncovered": uncovered_mask,
    }


def _panel(axis, image, mask, title: str, scale_bar: bool = False) -> None:
    low, high = _display_limits(image)
    axis.imshow(image.T, origin="lower", cmap="gray", vmin=low, vmax=high, interpolation="nearest")
    axis.contour(mask.T, levels=[0.5], colors=["#D55E00"], linewidths=0.9)
    if scale_bar:
        axis.plot([4, 24], [8, 8], color="white", lw=2, solid_capstyle="butt")
        axis.text(4, 12, "20 mm", color="white", fontsize=7, ha="left", va="bottom")
    axis.set_title(title, fontsize=8)
    axis.set_axis_off()


def write_slice_figure(result: dict, png_path: Path, pdf_path: Path) -> None:
    """Draw the observed visits and the prescribed 28-day step."""
    crop = result["_crop"]
    planes = result["_planes"]
    images = result["_images"]
    density = result["_density"]
    drawn = [visit for visit in VISITS if visit["drawn"]]
    titles = {
        "week-000-1": "Day 0\nPreoperative",
        "week-000-2": "Day 3\nPostoperative",
        "week-045": "Day 315\nProgressive disease",
        "week-049": "Day 343\nProgressive disease",
    }
    style = {"font.size": 9, "axes.spines.top": False, "axes.spines.right": False}
    with plt.rc_context(style):
        fig = plt.figure(figsize=(7.4, 5.6), layout="constrained")
        grid = fig.add_gridspec(2, 4)
        for column, visit in enumerate(drawn):
            axis = fig.add_subplot(grid[0, column])
            name = visit["name"]
            _panel(
                axis,
                images[name][:, :, result["axial_index"]][crop],
                planes[name][crop],
                titles[name],
                scale_bar=column == 0,
            )
        initial = planes["week-045"][crop]
        solved = density[crop]
        later = planes["week-049"][crop]
        axis = fig.add_subplot(grid[1, 0])
        axis.imshow(initial.T, origin="lower", cmap="gray", vmin=0, vmax=1, interpolation="nearest")
        axis.set_title("Day 315 indicator", fontsize=8)
        axis.set_axis_off()
        axis = fig.add_subplot(grid[1, 1])
        image = axis.imshow(
            solved.T, origin="lower", cmap="viridis", vmin=0, vmax=1, interpolation="nearest"
        )
        axis.set_title("Prescribed step, day 343", fontsize=8)
        axis.set_axis_off()
        fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
        axis = fig.add_subplot(grid[1, 2])
        axis.imshow(
            solved.T, origin="lower", cmap="viridis", vmin=0, vmax=1, interpolation="nearest"
        )
        axis.contour(
            (solved >= VISIBLE_THRESHOLD).T, levels=[0.5], colors=["#0072B2"], linewidths=0.9
        )
        axis.contour(later.T, levels=[0.5], colors=["#D55E00"], linewidths=0.9)
        axis.contour(
            result["_uncovered"][crop].T,
            levels=[0.5],
            colors=["#CC79A7"],
            linewidths=0.9,
        )
        axis.set_title("Threshold 0.5 and day-343 label", fontsize=8)
        axis.set_axis_off()
        fig.suptitle(
            "LUMIERE Patient-048, one axial post-contrast T1 slice",
            fontsize=11,
        )
        png_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_path, dpi=180)
        fig.savefig(pdf_path, metadata={"CreationDate": None, "ModDate": None})
        plt.close(fig)


def write_slice_tex(result: dict, path: Path) -> None:
    """Write manuscript macros for the areas and the prescribed-step discrepancy."""
    by_name = {visit["name"]: visit for visit in result["visits"]}
    initial = result["compartments_mm2"]["week-045"]
    later = result["compartments_mm2"]["week-049"]
    missed = result["largest_uncovered_component"]
    numbers = {
        "LumiereAxialIndex": str(result["axial_index"]),
        "LumiereAreaPre": str(by_name["week-000-1"]["whole_tumor_area_mm2"]),
        "LumiereAreaPost": str(by_name["week-000-2"]["whole_tumor_area_mm2"]),
        "LumiereAreaInitial": str(by_name["week-045"]["whole_tumor_area_mm2"]),
        "LumiereAreaLater": str(by_name["week-049"]["whole_tumor_area_mm2"]),
        "LumiereSimArea": str(result["simulated_area_mm2"]),
        "LumiereDice": f"{result['comparison_dice']:.3f}",
        "LumiereDiceBaseline": f"{result['baseline_dice']:.3f}",
        "LumiereDiceAlt": f"{result['alternative']['comparison_dice']:.3f}",
        "LumiereAltArea": str(result["alternative"]["simulated_area_mm2"]),
        "LumiereUncovered": str(result["largest_uncovered_component_mm2"]),
        "LumiereUncoveredEdema": str(missed["edema"]),
        "LumiereUncoveredEnhancing": str(missed["enhancing_tumor"]),
        "LumiereUncoveredNecrosis": str(missed["necrosis_or_non_enhancing"]),
        "LumiereMissDistanceInitial": f"{missed['min_distance_to_day315_whole_tumor_mm']:.1f}",
        "LumiereMissDistanceContour": f"{missed['min_distance_to_prescribed_contour_mm']:.1f}",
        "LumiereMissOffsetRight": f"{missed['offset_from_day315_centroid_right_mm']:.1f}",
        "LumiereMissOffsetAnterior": f"{missed['offset_from_day315_centroid_anterior_mm']:.1f}",
        "LumiereInitialEnhancing": str(initial["enhancing_tumor"]),
        "LumiereInitialEdema": str(initial["edema"]),
        "LumiereInitialNecrosis": str(initial["necrosis_or_non_enhancing"]),
        "LumiereLaterEnhancing": str(later["enhancing_tumor"]),
        "LumiereLaterEdema": str(later["edema"]),
        "LumiereLaterNecrosis": str(later["necrosis_or_non_enhancing"]),
        "LumiereDiffusivity": f"{DIFFUSIVITY_MM2_PER_DAY:.2f}",
        "LumiereAltDiffusivity": f"{ALTERNATIVE_DIFFUSIVITY_MM2_PER_DAY:.2f}",
        "LumiereProliferation": f"{PROLIFERATION_PER_DAY:.2f}",
        "LumiereElapsedDays": str(result["solved_interval_days"]),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "% Generated from the LUMIERE Patient-048 slice. Not a fitted growth rate.\n"
        + "".join(f"\\newcommand{{\\{key}}}{{{value}}}\n" for key, value in numbers.items())
    )


def write_lumiere_slice_illustration(output: Path, paper_dir: Path | None = None) -> dict | None:
    """Write the slice record and figure when the local extract is available."""
    root = lumiere_p048_root()
    if root is None:
        return None
    result = illustrate_patient048(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    write_slice_figure(
        result,
        output / "lumiere_p048_slice.png",
        output / "lumiere_p048_slice.pdf",
    )
    public = {key: value for key, value in result.items() if not key.startswith("_")}
    (output / "lumiere_p048_slice.json").write_text(
        json.dumps(public, indent=2, allow_nan=False) + "\n"
    )
    if paper_dir is not None:
        generated = Path(paper_dir)
        generated.mkdir(parents=True, exist_ok=True)
        write_slice_figure(
            result,
            generated / "lumiere_p048_slice.png",
            generated / "lumiere_p048_slice.pdf",
        )
        write_slice_tex(result, generated / "lumiere_p048.tex")
    return public
