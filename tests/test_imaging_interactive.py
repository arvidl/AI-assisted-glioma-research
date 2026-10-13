import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from glioma_ai.imaging_interactive import (
    blob_sweep,
    burden_scenario,
    constructed_regions,
    disc,
    draw_burden_state,
    draw_segmentation_state,
    regional_burden,
    segmentation_scenario,
)
from glioma_ai.metrics import hausdorff95_mm, surface_points_mm


def test_hd95_exact_cases_and_spacing():
    a = np.zeros((12, 5, 5), dtype=np.uint8)
    b = np.zeros_like(a)
    a[1, 2, 2] = 1
    b[6, 2, 2] = 1
    assert hausdorff95_mm(a, b) == pytest.approx(5.0)
    assert hausdorff95_mm(a, b, (2.0, 1.0, 1.0)) == pytest.approx(10.0)
    assert hausdorff95_mm(b, a) == hausdorff95_mm(a, b)
    assert hausdorff95_mm(a, a) == 0.0
    with pytest.raises(ValueError):
        hausdorff95_mm(a, np.zeros_like(a))


def test_surface_excludes_interior():
    cube = np.zeros((7, 7, 7), dtype=np.uint8)
    cube[1:6, 1:6, 1:6] = 1
    assert len(surface_points_mm(cube)) == 5**3 - 3**3


def test_concentric_discs_and_shift():
    inner, outer = disc((50, 50), 15), disc((50, 50), 19)
    assert hausdorff95_mm(outer, inner) == pytest.approx(4.0, abs=0.6)
    shifted = segmentation_scenario(shift_mm=4.0)
    assert shifted["hd95_mm"] == pytest.approx(4.0, abs=0.6)


def test_distant_blob_moves_hd95_much_more_than_dice():
    sweep = blob_sweep(0.0, 0.0, 30.0)
    assert sweep["dice"][0] == 1.0 and sweep["hd95_mm"][0] == 0.0
    assert sweep["dice"][-1] > 0.85
    assert sweep["hd95_mm"][-1] > 10.0
    assert sweep["hd95_mm"][1] < 1.0


def test_regional_burden_fractions_and_small_region_sensitivity():
    labels = constructed_regions()
    left = regional_burden(disc((15, 50), 8), labels)
    assert left["A"]["fraction_of_tumour"] == pytest.approx(1.0)
    run = burden_scenario()
    total = sum(v["fraction_of_tumour"] for v in run["reference_profile"].values())
    assert total == pytest.approx(1.0)
    assert run["dice"] > 0.85
    reference_s = run["reference_profile"]["S"]["fraction_of_region"]
    prediction_s = run["prediction_profile"]["S"]["fraction_of_region"]
    assert prediction_s - reference_s > 0.15


def test_imaging_figures_render():
    figure = plt.figure()
    draw_segmentation_state(figure, segmentation_scenario(2, 0, 3), blob_sweep(2, 0, 30))
    plt.close(figure)
    figure = plt.figure()
    draw_burden_state(figure, burden_scenario())
    assert len(figure.axes) == 2
    plt.close(figure)
