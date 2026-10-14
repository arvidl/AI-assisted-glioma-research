"""Synthetic segmentation-metric and regional-burden demonstrations for notebook 09.

All masks and regions are constructed on a single 1 mm x 1 mm slice (stored as a
3D array with one slice). Region names are letters, not anatomical labels. Nothing
here reruns or reproduces the published SegResNet pipeline.
"""

import numpy as np

from glioma_ai.metrics import dice_score, hausdorff95_mm, surface_points_mm
from glioma_ai.notebook_display import show_figure

GRID = 100
SPACING_MM = (1.0, 1.0, 1.0)
REGION_NAMES = ("A", "B", "C", "S")
REGION_COLOURS = ("#d9e6f2", "#e8e1f0", "#e5efe0", "#f6d7a7")


def disc(centre_mm, radius_mm, size: int = GRID) -> np.ndarray:
    """Binary disc on a size x size x 1 grid with 1 mm voxels; centre in (x, y) mm."""
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    inside = (x - centre_mm[0]) ** 2 + (y - centre_mm[1]) ** 2 <= radius_mm**2
    return inside[:, :, None].astype(np.uint8)


def segmentation_scenario(
    shift_mm: float = 0.0,
    dilation_mm: float = 0.0,
    blob_radius_mm: float = 0.0,
    blob_distance_mm: float = 30.0,
    radius_mm: float = 15.0,
) -> dict:
    """A reference disc and a 'prediction' that is shifted, dilated and may add a blob."""
    centre = (GRID / 2, GRID / 2)
    reference = disc(centre, radius_mm)
    prediction = disc((centre[0] + shift_mm, centre[1]), max(radius_mm + dilation_mm, 1.0))
    if blob_radius_mm > 0:
        blob = disc((centre[0], centre[1] + blob_distance_mm), blob_radius_mm)
        prediction = np.maximum(prediction, blob)
    reference_area = int(reference.sum())
    return {
        "reference": reference,
        "prediction": prediction,
        "dice": dice_score(prediction, reference),
        "hd95_mm": hausdorff95_mm(prediction, reference, SPACING_MM),
        "hd_max_mm": _max_surface_distance(prediction, reference),
        "area_error": (int(prediction.sum()) - reference_area) / reference_area,
        "parameters": {
            "shift_mm": shift_mm,
            "dilation_mm": dilation_mm,
            "blob_radius_mm": blob_radius_mm,
            "blob_distance_mm": blob_distance_mm,
            "radius_mm": radius_mm,
        },
    }


def _max_surface_distance(prediction, reference) -> float:
    a = surface_points_mm(prediction, SPACING_MM)
    b = surface_points_mm(reference, SPACING_MM)
    forward = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    backward = np.sqrt(((b[:, None, :] - a[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    return float(max(forward.max(), backward.max()))


def blob_sweep(shift_mm, dilation_mm, blob_distance_mm, radii=tuple(range(9))) -> dict:
    """Dice and HD95 as a distant false-positive blob grows, other settings fixed."""
    runs = [segmentation_scenario(shift_mm, dilation_mm, float(r), blob_distance_mm) for r in radii]
    return {
        "radii_mm": np.asarray(radii, dtype=float),
        "dice": np.array([run["dice"] for run in runs]),
        "hd95_mm": np.array([run["hd95_mm"] for run in runs]),
    }


OVERLAY_COLOURS = {
    "both": (0.35, 0.65, 0.45),
    "prediction only": (0.85, 0.45, 0.3),
    "reference only": (0.35, 0.5, 0.85),
}


def _overlay(axis, reference, prediction, title, extent=None):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    ref, pred = reference[:, :, 0].astype(bool), prediction[:, :, 0].astype(bool)
    image = np.ones((*ref.shape, 3))
    image[ref & pred] = OVERLAY_COLOURS["both"]
    image[pred & ~ref] = OVERLAY_COLOURS["prediction only"]
    image[ref & ~pred] = OVERLAY_COLOURS["reference only"]
    axis.imshow(np.transpose(image, (1, 0, 2)), origin="lower")
    axis.contour(ref.T.astype(float), levels=[0.5], colors="black", linewidths=0.8)
    axis.set(title=title, xlabel="Constructed x (mm)", ylabel="Constructed y (mm)")
    handles = [
        Patch(color=OVERLAY_COLOURS["both"], label="Both (TP)"),
        Patch(color=OVERLAY_COLOURS["prediction only"], label="Prediction only (FP)"),
        Patch(color=OVERLAY_COLOURS["reference only"], label="Reference only (FN)"),
        Line2D([], [], color="black", linewidth=0.8, label="Reference boundary"),
    ]
    axis.legend(handles=handles, loc="upper right", fontsize=7.5, framealpha=0.85)


def draw_segmentation_state(figure, run, sweep):
    figure.clear()
    overlay, curves = figure.subplots(1, 2, gridspec_kw={"width_ratios": [1, 1.3]})
    _overlay(
        overlay,
        run["reference"],
        run["prediction"],
        "Prediction versus reference",
    )
    overlay.text(
        2,
        3,
        f"Dice {run['dice']:.3f}\nHD95 {run['hd95_mm']:.1f} mm\n"
        f"Max distance {run['hd_max_mm']:.1f} mm\n"
        f"Area error {100 * run['area_error']:+.0f}%",
        fontsize=9,
        va="bottom",
        bbox={"facecolor": "white", "alpha": 0.85},
    )
    curves.plot(sweep["radii_mm"], sweep["dice"], "o-", color="#31858f", label="Dice (left axis)")
    curves.set(
        xlabel="Radius of distant false-positive blob (mm)",
        ylabel="Dice",
        ylim=(0, 1.02),
        title="Same main error; a growing distant blob",
    )
    twin = curves.twinx()
    twin.plot(
        sweep["radii_mm"], sweep["hd95_mm"], "s--", color="#d67645", label="HD95 (right axis)"
    )
    twin.set_ylabel("HD95 (mm)")
    lines = curves.get_lines() + twin.get_lines()
    curves.legend(lines, [line.get_label() for line in lines], fontsize=8, loc="center right")
    p = run["parameters"]
    figure.suptitle(
        f"Constructed slice, 1 mm voxels: reference disc r = {p['radius_mm']:g} mm; prediction "
        f"shifted {p['shift_mm']:g} mm, dilated {p['dilation_mm']:g} mm, blob "
        f"r = {p['blob_radius_mm']:g} mm at {p['blob_distance_mm']:g} mm"
    )
    figure.tight_layout()


def _panel(widgets, controls, show):
    return widgets.VBox([*controls.values(), widgets.interactive_output(show, controls)])


def _sliders(widgets, specs):
    style = {"description_width": "15em"}
    layout = widgets.Layout(width="36em")
    return {
        name: widgets.FloatSlider(
            value=value,
            min=low,
            max=high,
            step=step,
            description=label,
            continuous_update=False,
            style=style,
            layout=layout,
        )
        for name, (value, low, high, step, label) in specs.items()
    }


def segmentation_explorer():
    """Sliders for shift, dilation and the distant blob's radius and distance."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    controls = _sliders(
        widgets,
        {
            "shift_mm": (2.0, -10.0, 10.0, 1.0, "Prediction shift (mm)"),
            "dilation_mm": (0.0, -5.0, 5.0, 1.0, "Dilation (+) / erosion (−) (mm)"),
            "blob_radius_mm": (3.0, 0.0, 8.0, 1.0, "False-positive blob radius (mm)"),
            "blob_distance_mm": (30.0, 20.0, 45.0, 1.0, "Blob distance from centre (mm)"),
        },
    )

    def show(shift_mm, dilation_mm, blob_radius_mm, blob_distance_mm):
        figure = plt.figure(figsize=(12.5, 5))
        draw_segmentation_state(
            figure,
            segmentation_scenario(shift_mm, dilation_mm, blob_radius_mm, blob_distance_mm),
            blob_sweep(shift_mm, dilation_mm, blob_distance_mm),
        )
        show_figure(figure)

    return _panel(widgets, controls, show)


def constructed_regions(size: int = GRID) -> np.ndarray:
    """Integer label slice: bands A (x < 35), B (35-64), C (x >= 65) and a small region S."""
    x, y = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    labels = np.where(x < 35, 1, np.where(x < 65, 2, 3))
    labels[(x >= 62) & (x <= 67) & (y >= 47) & (y <= 53)] = 4
    return labels[:, :, None]


def regional_burden(mask, labels, voxel_volume_mm3: float = 1.0) -> dict:
    """Overlap of a tumour mask with each labelled region, in native grid units.

    Returns, per region name, the overlap volume (mm³; mm² × 1 mm slice here), the
    fraction of the tumour in that region and the fraction of the region involved.
    """
    tumour = np.asarray(mask).astype(bool)
    labels = np.asarray(labels)
    if tumour.shape != labels.shape:
        raise ValueError("Mask and region labels must share a grid.")
    total = tumour.sum()
    result = {}
    for index, name in enumerate(REGION_NAMES, start=1):
        region = labels == index
        overlap = int((tumour & region).sum())
        result[name] = {
            "overlap_mm3": overlap * voxel_volume_mm3,
            "fraction_of_tumour": overlap / total if total else 0.0,
            "fraction_of_region": overlap / int(region.sum()) if region.any() else 0.0,
        }
    return result


def burden_scenario(
    centre_x_mm: float = 50.0,
    centre_y_mm: float = 50.0,
    radius_mm: float = 11.0,
    prediction_shift_mm: float = 2.0,
) -> dict:
    """Reference and shifted-prediction tumours with their regional profiles."""
    labels = constructed_regions()
    reference = disc((centre_x_mm, centre_y_mm), radius_mm)
    prediction = disc((centre_x_mm + prediction_shift_mm, centre_y_mm), radius_mm)
    return {
        "labels": labels,
        "reference": reference,
        "prediction": prediction,
        "dice": dice_score(prediction, reference),
        "reference_profile": regional_burden(reference, labels),
        "prediction_profile": regional_burden(prediction, labels),
        "parameters": {
            "centre_x_mm": centre_x_mm,
            "centre_y_mm": centre_y_mm,
            "radius_mm": radius_mm,
            "prediction_shift_mm": prediction_shift_mm,
        },
    }


def draw_burden_state(figure, run):
    figure.clear()
    plane, bars = figure.subplots(1, 2, gridspec_kw={"width_ratios": [1, 1.2]})
    labels = run["labels"][:, :, 0]
    from matplotlib.colors import ListedColormap

    plane.imshow(labels.T, origin="lower", cmap=ListedColormap(REGION_COLOURS), vmin=0.5, vmax=4.5)
    for index, name in enumerate(REGION_NAMES, start=1):
        xs, ys = np.nonzero(labels == index)
        plane.text(
            xs.mean(),
            ys.mean() if name != "S" else ys.max() + 3,
            name,
            ha="center",
            fontsize=11,
            weight="bold",
        )
    plane.contour(
        run["reference"][:, :, 0].T.astype(float), levels=[0.5], colors="black", linewidths=1.2
    )
    plane.contour(
        run["prediction"][:, :, 0].T.astype(float),
        levels=[0.5],
        colors="#d67645",
        linewidths=1.2,
        linestyles="--",
    )
    plane.set(
        title="Constructed regions; black: reference, dashed: prediction",
        xlabel="Constructed x (mm)",
        ylabel="Constructed y (mm)",
    )
    positions = np.arange(len(REGION_NAMES))
    reference = [run["reference_profile"][n]["fraction_of_region"] for n in REGION_NAMES]
    prediction = [run["prediction_profile"][n]["fraction_of_region"] for n in REGION_NAMES]
    bars.bar(positions - 0.2, reference, 0.4, color="#444444", label="Reference")
    bars.bar(positions + 0.2, prediction, 0.4, color="#d67645", label="Prediction")
    bars.set_xticks(positions, REGION_NAMES)
    bars.set(
        ylabel="Fraction of region involved",
        ylim=(0, max(0.25, 1.15 * max(reference + prediction))),
        title=f"Regional profile (hit-plot style); Dice {run['dice']:.3f}",
    )
    bars.legend(fontsize=8)
    p = run["parameters"]
    figure.suptitle(
        f"Synthetic regional burden: tumour r = {p['radius_mm']:g} mm at "
        f"({p['centre_x_mm']:g}, {p['centre_y_mm']:g}) mm; prediction shifted "
        f"{p['prediction_shift_mm']:g} mm in x. Regions are letters, not anatomy."
    )
    figure.tight_layout()


def burden_explorer():
    """Sliders for tumour position and size and the prediction's shift."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    controls = _sliders(
        widgets,
        {
            "centre_x_mm": (50.0, 15.0, 85.0, 1.0, "Tumour centre x (mm)"),
            "centre_y_mm": (50.0, 15.0, 85.0, 1.0, "Tumour centre y (mm)"),
            "radius_mm": (11.0, 3.0, 20.0, 1.0, "Tumour radius (mm)"),
            "prediction_shift_mm": (2.0, -6.0, 6.0, 1.0, "Prediction shift in x (mm)"),
        },
    )

    def show(**values):
        figure = plt.figure(figsize=(12.5, 5))
        draw_burden_state(figure, burden_scenario(**values))
        show_figure(figure)

    return _panel(widgets, controls, show)
