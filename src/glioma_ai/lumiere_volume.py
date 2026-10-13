"""Patient-048 in 3D: cropped prepared volumes, an explicit tissue map and 3D scoring.

Reads the investigator's prepared 1 mm RAS grid (registered CT1 and MONAI BraTS
labels at weeks 045 and 049) and, if present, the FreeSurfer ``wmparc`` that the
companion pipeline computed on the week-045 T1 on the same grid. Nothing is
registered, resampled, segmented or relabelled: FreeSurfer labels are grouped
into CSF, grey and white matter by the explicit tables below, and every label
outside them is reported and kept outside the growth domain. The reading,
coefficients and two-level start are those of ``lumiere_biology``.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from glioma_ai.growth_volume import VolumeRun, simulate_density_3d
from glioma_ai.lumiere_biology import (
    LITERATURE,
    T1GD_FRACTION,
    T2_FRACTION,
    WHOLE_LABELS,
    front_speed_mm_per_day,
)
from glioma_ai.lumiere_dynamics import CORE_LABELS, _image_header, _save
from glioma_ai.lumiere_slice import _require_label_scheme
from glioma_ai.provenance import sha256

INITIAL, LATER = "week-045", "week-049"
INTERVAL_DAYS = 28
CROP_MARGIN_MM = 25
OUTSIDE, CSF, GREY, WHITE = 0, 1, 2, 3
TISSUE_NAMES = {
    OUTSIDE: "outside / unclassified",
    CSF: "CSF",
    GREY: "grey matter",
    WHITE: "white matter",
}
CSF_LABELS = (4, 5, 14, 15, 24, 31, 43, 44, 63, 72)
GREY_LABELS = (3, 8, 10, 11, 12, 13, 17, 18, 26, 28, 42, 47, 49, 50, 51, 52, 53, 54, 58, 60)
WHITE_LABELS = (2, 7, 16, 41, 46, 77, 85, 251, 252, 253, 254, 255, 5001, 5002)
GREY_RANGES = ((1000, 1036), (2000, 2036))
WHITE_RANGES = ((3000, 3036), (4000, 4036))
WHITE_TO_GREY = 5.0
TISSUE_SOURCE = (
    "Swanson KR, Alvord EC Jr, Murray JD, Cell Prolif 33:317-329 (2000), "
    "doi:10.1046/j.1365-2184.2000.00177.x (D_white = 5 D_grey); 5 is called a first "
    "approximation within an estimated 2-100-fold range in Swanson et al., "
    "Br J Cancer 86:14-18 (2002), doi:10.1038/sj.bjc.6600021, which also closes CSF boundaries"
)


def tissue_classes(wmparc: np.ndarray) -> tuple[np.ndarray, dict]:
    """Group FreeSurfer labels into CSF, grey and white matter by explicit tables."""
    labels = np.asarray(wmparc).astype(np.int64)
    tissue = np.zeros(labels.shape, dtype=np.int8)
    tissue[np.isin(labels, CSF_LABELS)] = CSF
    grey = np.isin(labels, GREY_LABELS)
    white = np.isin(labels, WHITE_LABELS)
    for low, high in GREY_RANGES:
        grey |= (labels >= low) & (labels < high)
    for low, high in WHITE_RANGES:
        white |= (labels >= low) & (labels < high)
    tissue[grey] = GREY
    tissue[white] = WHITE
    unclassified = sorted(int(v) for v in np.unique(labels[(tissue == OUTSIDE) & (labels != 0)]))
    return tissue, {"unclassified_labels": unclassified}


def component_labels_3d(mask: np.ndarray) -> np.ndarray:
    """Face-connected (6-neighbour) component labels of a 3D boolean mask."""
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 3:
        raise ValueError("Component labelling requires a 3D mask.")
    padded = np.pad(mask, 1)
    flat = padded.ravel()
    labels = np.zeros(flat.shape, dtype=np.int32)
    ny, nz = padded.shape[1], padded.shape[2]
    offsets = (1, -1, nz, -nz, ny * nz, -ny * nz)
    current = 0
    for seed in np.flatnonzero(flat):
        if labels[seed]:
            continue
        current += 1
        labels[seed] = current
        stack = [int(seed)]
        while stack:
            index = stack.pop()
            for offset in offsets:
                neighbour = index + offset
                if flat[neighbour] and not labels[neighbour]:
                    labels[neighbour] = current
                    stack.append(neighbour)
    return labels.reshape(padded.shape)[1:-1, 1:-1, 1:-1]


@dataclass
class VolumeCase:
    """Cropped weeks 045 and 049, the optional week-045 tissue map, and full-volume counts."""

    ct1: dict
    labels: dict
    tissue: np.ndarray | None
    split: dict
    metadata: dict

    def roi(self, visit: str, selected: tuple[int, ...]) -> np.ndarray:
        return np.isin(self.labels[visit], selected)


def load_volume_case(root: Path, *, margin_mm: int = CROP_MARGIN_MM) -> VolumeCase:
    """Read weeks 045 and 049 (and the week-045 wmparc if present); crop around week 045.

    The crop is the week-045 whole-tumour box plus ``margin_mm``; it uses no later
    data. Local and distant week-049 components are found on the full volume.
    """
    root = Path(root)
    images, label_maps, hashes, reference = {}, {}, {}, None
    for visit in (INITIAL, LATER):
        base = root / "derivatives" / f"tp-{visit}"
        label_path = base / "seg_dl" / f"tp-{visit}_seg_brats3_dl.nii.gz"
        record_path = label_path.with_name(f"tp-{visit}_seg_brats3_dl.json")
        image_path = base / f"tp-{visit}_CT1_to_ref.nii.gz"
        _require_label_scheme(record_path)
        image, label = _image_header(image_path), _image_header(label_path, label=True)
        for other in (label, *(() if reference is None else (reference,))):
            if other.shape != image.shape or not np.allclose(other.affine, image.affine, atol=1e-3):
                raise ValueError(f"{visit} is not on the prepared grid; no alignment attempted.")
        reference = reference or image
        values = np.asarray(label.dataobj)
        if not np.isin(values, (0, 1, 2, 4)).all():
            raise ValueError(f"Unknown labels at {visit}; no relabelling attempted.")
        images[visit] = np.asarray(image.dataobj, dtype=np.float32)
        label_maps[visit] = values.astype(np.uint8)
        for path in (image_path, label_path, record_path):
            hashes[str(path.relative_to(root))] = sha256(path)
    parcellation = (
        root
        / "derivatives"
        / f"tp-{INITIAL}"
        / "parcellation"
        / f"tp-{INITIAL}_wmparc_native.nii.gz"
    )
    tissue, tissue_record = None, None
    if parcellation.is_file():
        wmparc = _image_header(parcellation, label=True)
        if wmparc.shape != reference.shape or not np.allclose(
            wmparc.affine, reference.affine, atol=1e-3
        ):
            raise ValueError("The wmparc is not on the prepared grid; no resampling attempted.")
        tissue, tissue_record = tissue_classes(np.asarray(wmparc.dataobj))
        record = parcellation.with_name(f"tp-{INITIAL}_wmparc.json")
        hashes[str(parcellation.relative_to(root))] = sha256(parcellation)
        if record.is_file():
            hashes[str(record.relative_to(root))] = sha256(record)
            meta = json.loads(record.read_text())
            tissue_record.update(
                {"software": meta.get("version"), "input_channel": meta.get("input_channel")}
            )

    start_whole = np.isin(label_maps[INITIAL], WHOLE_LABELS)
    later_whole = np.isin(label_maps[LATER], WHOLE_LABELS)
    later_core = np.isin(label_maps[LATER], CORE_LABELS)
    components = component_labels_3d(later_whole)
    touching = np.unique(components[start_whole & later_whole])
    touching = touching[touching > 0]
    local = np.isin(components, touching)
    sizes = np.bincount(components.ravel())[1:]
    distant_sizes = sorted(
        (int(sizes[k - 1]) for k in range(1, len(sizes) + 1) if k not in touching), reverse=True
    )

    box = np.argwhere(start_whole)
    low = np.maximum(box.min(axis=0) - margin_mm, 0)
    high = np.minimum(box.max(axis=0) + margin_mm + 1, start_whole.shape)
    crop = tuple(slice(int(a), int(b)) for a, b in zip(low, high, strict=True))
    voxel_mm3 = float(np.prod(np.linalg.norm(reference.affine[:3, :3], axis=0)))
    cm3 = voxel_mm3 / 1000

    def volume(mask):
        return float(mask.sum() * cm3)

    split = {
        "local_whole": local[crop],
        "local_core": (later_core & local)[crop],
        "local_whole_total": int(local.sum()),
        "local_core_total": int((later_core & local).sum()),
        "distant_whole_total": int((later_whole & ~local).sum()),
        "distant_in_crop": (later_whole & ~local)[crop],
        "local_full": local,
    }
    observed = {
        "start_core_cm3": volume(np.isin(label_maps[INITIAL], CORE_LABELS)),
        "start_whole_cm3": volume(start_whole),
        "later_core_cm3": volume(later_core),
        "later_whole_cm3": volume(later_whole),
        "local_whole_cm3": volume(local),
        "local_core_cm3": volume(later_core & local),
        "distant_whole_cm3": volume(later_whole & ~local),
        "n_later_components": int(len(sizes)),
        "n_local_components": int(len(touching)),
        "largest_distant_component_cm3": distant_sizes[0] * cm3 if distant_sizes else 0.0,
    }
    return VolumeCase(
        ct1={visit: image[crop] for visit, image in images.items()},
        labels={visit: values[crop] for visit, values in label_maps.items()},
        tissue=None if tissue is None else tissue[crop],
        split=split,
        metadata={
            "schema": "lumiere-volume-v1",
            "public_case": "LUMIERE-048",
            "visits": [INITIAL, LATER],
            "interval_days": INTERVAL_DAYS,
            "grid": "prepared 1 mm RAS reference grid; registration supplied upstream",
            "volume_shape": list(reference.shape),
            "crop_start": [int(v) for v in low],
            "crop_shape": [int(b - a) for a, b in zip(low, high, strict=True)],
            "crop_rule": f"week-045 whole-tumour box plus {margin_mm} mm; later data not used",
            "voxel_mm3": voxel_mm3,
            "connectivity": "6-neighbour (face) components of the week-049 whole union",
            "observed": observed,
            "tissue": tissue_record,
            "source_sha256": hashes,
        },
    )


def two_level_initial_3d(case: VolumeCase, core_level: float = 0.9, margin_level: float = 0.36):
    if not T1GD_FRACTION <= core_level <= 1 or not T2_FRACTION <= margin_level < T1GD_FRACTION:
        raise ValueError("Require 0.80 <= core level <= 1 and 0.16 <= margin level < 0.80.")
    core, whole = case.roi(INITIAL, CORE_LABELS), case.roi(INITIAL, WHOLE_LABELS)
    return np.where(core, core_level, np.where(whole, margin_level, 0.0))


def growth_domain(case: VolumeCase, kind: str) -> np.ndarray:
    """``brain``: CT1 support; ``parenchyma``: FreeSurfer grey or white matter.

    Both add the week-045 labels, so no starting density lies outside the domain.
    """
    labelled = case.roi(INITIAL, WHOLE_LABELS)
    if kind == "brain":
        return (case.ct1[INITIAL] > 0) | labelled
    if kind == "parenchyma":
        if case.tissue is None:
            raise ValueError("The parenchyma domain needs the week-045 wmparc.")
        return np.isin(case.tissue, (GREY, WHITE)) | labelled
    raise ValueError("Domain must be 'brain' or 'parenchyma'.")


def tissue_diffusivity(
    case: VolumeCase, mean_d: float, domain: np.ndarray
) -> tuple[np.ndarray, dict]:
    """D_white = 5 D_grey, scaled so that the domain mean equals ``mean_d``.

    Week-045 tumour voxels that FreeSurfer did not call grey or white matter get
    ``mean_d``; FreeSurfer is not reliable inside the lesion.
    """
    if case.tissue is None:
        raise ValueError("Tissue-weighted diffusivity needs the week-045 wmparc.")
    grey = domain & (case.tissue == GREY)
    white = domain & (case.tissue == WHITE)
    other = domain & ~grey & ~white
    n_grey, n_white, n_other = int(grey.sum()), int(white.sum()), int(other.sum())
    d_grey = mean_d * (n_grey + n_white) / (n_grey + WHITE_TO_GREY * n_white)
    field = np.zeros(domain.shape)
    field[grey], field[white], field[other] = d_grey, WHITE_TO_GREY * d_grey, mean_d
    return field, {
        "d_grey_mm2_per_day": float(d_grey),
        "d_white_mm2_per_day": float(WHITE_TO_GREY * d_grey),
        "d_lesion_unclassified_mm2_per_day": float(mean_d),
        "domain_fractions": {
            "grey": n_grey / domain.sum(),
            "white": n_white / domain.sum(),
            "lesion_unclassified": n_other / domain.sum(),
        },
    }


def _dice(prediction: np.ndarray, observed: np.ndarray, observed_total: int) -> float:
    total = int(prediction.sum()) + observed_total
    return float(2 * np.count_nonzero(prediction & observed) / total) if total else 1.0


def score_volume(density: np.ndarray, case: VolumeCase, voxel_mm3: float) -> dict:
    """Two-level reading scored against the week-049 local labels on the full volume."""
    split = case.split
    core, whole = density >= T1GD_FRACTION, density >= T2_FRACTION
    core_dice = _dice(core, split["local_core"], split["local_core_total"])
    whole_dice = _dice(whole, split["local_whole"], split["local_whole_total"])
    return {
        "core_cm3": float(core.sum() * voxel_mm3 / 1000),
        "whole_cm3": float(whole.sum() * voxel_mm3 / 1000),
        "local_core_dice": core_dice,
        "local_whole_dice": whole_dice,
        "local_score": 0.5 * (core_dice + whole_dice),
        "distant_reached_cm3": float((whole & split["distant_in_crop"]).sum() * voxel_mm3 / 1000),
    }


def run_volume(
    case: VolumeCase,
    *,
    diffusivity_mm2_per_day: float = LITERATURE["diffusivity_mm2_per_day"],
    rho_per_day: float = LITERATURE["rho_per_day"],
    domain: str = "brain",
    tissue_weighted: bool = False,
    core_level: float = 0.9,
    margin_level: float = 0.36,
    dt_days: float = 0.2,
    snapshot_days: tuple[float, ...] = (0, 7, 14, 21, 28),
) -> dict:
    """One 3D forward run from week 045, read and scored at week 049 (day 28)."""
    if snapshot_days[-1] != INTERVAL_DAYS:
        raise ValueError("The last snapshot must be the week-049 visit, day 28.")
    inside = growth_domain(case, domain)
    initial = two_level_initial_3d(case, core_level, margin_level)
    field, tissue = diffusivity_mm2_per_day, None
    if tissue_weighted:
        field, tissue = tissue_diffusivity(case, diffusivity_mm2_per_day, inside)
    run: VolumeRun = simulate_density_3d(
        initial, field, rho_per_day, snapshot_days, dt_days=dt_days, domain=inside
    )
    voxel = case.metadata["voxel_mm3"]
    final = run.density[-1]
    faces = (final[0], final[-1], final[:, 0], final[:, -1], final[:, :, 0], final[:, :, -1])
    local = case.split["local_whole"]
    return {
        "settings": {
            "diffusivity_mm2_per_day": float(diffusivity_mm2_per_day),
            "rho_per_day": float(rho_per_day),
            "domain": domain,
            "tissue_weighted": tissue_weighted,
            "core_level": core_level,
            "margin_level": margin_level,
            "dt_days": run.largest_step_days,
            "n_steps": run.n_steps,
        },
        "tissue": tissue,
        "front_speed_mm_per_day": front_speed_mm_per_day(diffusivity_mm2_per_day, rho_per_day),
        "model": score_volume(final, case, voxel),
        "no_change": score_volume(initial, case, voxel),
        "core_cm3_by_day": run.volumes_cm3(T1GD_FRACTION).tolist(),
        "whole_cm3_by_day": run.volumes_cm3(T2_FRACTION).tolist(),
        "days": run.days.tolist(),
        "local_outside_domain_fraction": float((local & ~inside).sum() / max(local.sum(), 1)),
        "max_density_on_crop_faces": float(max(face.max() for face in faces)),
        "max_balance_residual_mm3": run.max_balance_residual_mm3,
        "domain_mask": inside,
        "density": final,
    }


def compare_volume_variants(case: VolumeCase, fit: dict | None = None) -> dict:
    """Published medians with three anatomical assumptions, and the 2D fit carried to 3D."""
    runs = {"Literature, brain support": run_volume(case)}
    if case.tissue is not None:
        runs["Literature, parenchyma (CSF closed)"] = run_volume(case, domain="parenchyma")
        runs["Literature, parenchyma, white = 5 × grey"] = run_volume(
            case, domain="parenchyma", tissue_weighted=True
        )
    if fit is not None:
        values = {
            "diffusivity_mm2_per_day": fit["diffusivity_mm2_per_day"],
            "rho_per_day": fit["rho_per_day"],
        }
        runs["2D fit, brain support"] = run_volume(case, **values)
        if case.tissue is not None:
            runs["2D fit, parenchyma, white = 5 × grey"] = run_volume(
                case, domain="parenchyma", tissue_weighted=True, **values
            )
    return runs


def _centre(case: VolumeCase) -> tuple[int, int, int]:
    return tuple(
        int(v) for v in np.round(np.argwhere(case.roi(INITIAL, WHOLE_LABELS)).mean(axis=0))
    )


def _planes(volume: np.ndarray, centre: tuple[int, int, int]) -> list[np.ndarray]:
    i, j, k = centre
    return [volume[:, :, k], volume[:, j, :], volume[i, :, :]]


PLANE_TITLES = ("Axial", "Coronal", "Sagittal")
PLANE_AXES = (("R (mm)", "A (mm)"), ("R (mm)", "S (mm)"), ("A (mm)", "S (mm)"))


def write_volume_figure(case: VolumeCase, result: dict, output: Path, name: str) -> Path:
    """Tissue map and start (top); model reading against week-049 labels (bottom)."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    centre = _centre(case)
    start = two_level_initial_3d(
        case, result["settings"]["core_level"], result["settings"]["margin_level"]
    )
    figure, axes = plt.subplots(2, 3, figsize=(14, 9.5), constrained_layout=True)
    tissue_colors = ListedColormap(["#5b8fd6", "#9a9a9a", "#f2f2f2"])
    for column in range(3):
        top, bottom = axes[0, column], axes[1, column]
        ct1_start = _planes(case.ct1[INITIAL], centre)[column]
        ct1_later = _planes(case.ct1[LATER], centre)[column]
        for axis, image in ((top, ct1_start), (bottom, ct1_later)):
            positive = image[image > 0]
            high = np.percentile(positive, 99) if positive.size else 1
            axis.imshow(image.T, origin="lower", cmap="gray", vmin=0, vmax=high)
        if case.tissue is not None:
            tissue = _planes(case.tissue, centre)[column].astype(float)
            top.imshow(
                np.ma.masked_equal(tissue, OUTSIDE).T,
                origin="lower",
                cmap=tissue_colors,
                vmin=1,
                vmax=3,
                alpha=0.45,
            )
        top.contour(
            _planes(result["domain_mask"], centre)[column].T,
            [0.5],
            colors="#ffd166",
            linewidths=0.7,
        )
        for density, axis, style in ((start, top, "solid"), (result["density"], bottom, "solid")):
            plane = _planes(density, centre)[column]
            axis.contour(
                (plane >= T1GD_FRACTION).T,
                [0.5],
                colors="#f29b38",
                linewidths=1.4,
                linestyles=style,
            )
            axis.contour(
                (plane >= T2_FRACTION).T, [0.5], colors="#48dbbf", linewidths=1.4, linestyles=style
            )
        for mask, color in (
            (case.split["local_core"], "#f29b38"),
            (case.split["local_whole"], "#48dbbf"),
        ):
            plane = _planes(mask, centre)[column]
            if plane.any():
                bottom.contour(plane.T, [0.5], colors=color, linewidths=1.0, linestyles="dashed")
        distant = _planes(case.split["distant_in_crop"], centre)[column]
        if distant.any():
            bottom.imshow(
                np.ma.masked_equal(distant.astype(float), 0).T,
                origin="lower",
                cmap=ListedColormap(["#ff4fa3"]),
                alpha=0.5,
            )
        top.set_title(f"{PLANE_TITLES[column]}: week-045 start and week-045 tissue map")
        bottom.set_title(f"{PLANE_TITLES[column]}: model at day 28 on week-049 CT1")
        for axis in (top, bottom):
            axis.set_xlabel(PLANE_AXES[column][0])
            axis.set_ylabel(PLANE_AXES[column][1])
            axis.set_aspect("equal")
    handles = [
        Line2D([0], [0], color="#f29b38", lw=2, label="core reading c ≥ 0.80"),
        Line2D([0], [0], color="#48dbbf", lw=2, label="T2/FLAIR reading c ≥ 0.16"),
        Line2D([0], [0], color="grey", lw=1.5, ls="--", label="week-049 local labels"),
        Patch(color="#ff4fa3", alpha=0.5, label="week-049 distant labels"),
        Line2D([0], [0], color="#ffd166", lw=1, label="growth domain"),
        Patch(color="#5b8fd6", alpha=0.6, label="CSF"),
        Patch(color="#9a9a9a", alpha=0.6, label="grey matter"),
        Patch(color="#f2f2f2", alpha=0.9, label="white matter"),
    ]
    figure.legend(handles=handles, loc="outside lower center", ncols=4)
    figure.suptitle(
        "Patient-048, crop of the prepared 1 mm RAS grid through the week-045 lesion centre; "
        "axes in crop millimetres toward patient right (R), anterior (A) and superior (S)"
    )
    _save(figure, output, name)
    return output / f"{name}.png"


def write_volume_curves(case: VolumeCase, runs: dict, output: Path, name: str) -> Path:
    """Model volumes over 28 days against the observed week-045 and week-049 volumes."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    observed = case.metadata["observed"]
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    for label, result in runs.items():
        axes[0].plot(result["days"], result["core_cm3_by_day"], marker=".", label=label)
        axes[1].plot(result["days"], result["whole_cm3_by_day"], marker=".", label=label)
    for axis, start, local, total, title in (
        (
            axes[0],
            observed["start_core_cm3"],
            observed["local_core_cm3"],
            observed["later_core_cm3"],
            "Core reading (c ≥ 0.80) vs core labels",
        ),
        (
            axes[1],
            observed["start_whole_cm3"],
            observed["local_whole_cm3"],
            observed["later_whole_cm3"],
            "T2/FLAIR reading (c ≥ 0.16) vs whole labels",
        ),
    ):
        axis.plot(
            [0, INTERVAL_DAYS],
            [start, local],
            "ks--",
            label="observed local component (line joins two visits)",
        )
        axis.plot([INTERVAL_DAYS], [total], "k^", label="observed, all week-049 labels")
        axis.set_xlabel("Days after week 045 (nominal)")
        axis.set_ylabel("Volume (cm³)")
        axis.set_title(title)
    axes[1].legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
    _save(figure, output, name)
    return output / f"{name}.png"
