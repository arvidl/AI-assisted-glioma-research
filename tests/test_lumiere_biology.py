import numpy as np
import pytest

from glioma_ai import lumiere_biology as lb
from glioma_ai.growth_model import simulate_density_2d
from glioma_ai.lumiere_dynamics import SliceCase

VISITS = ["week-000-1", "week-000-2", "week-013", "week-023", "week-045", "week-049"]


def synthetic_case() -> SliceCase:
    """Brain disc; week 045 has core + margin; week 049 has a larger lesion and a distant one."""
    n = 64
    y, x = np.mgrid[:n, :n]
    radius = np.hypot(y - 32, x - 32)
    images = np.repeat((radius < 28)[None].astype(float) * 100, 6, axis=0)
    labels = np.zeros((6, n, n), dtype=np.uint8)
    labels[4][radius < 9] = 2
    labels[4][radius < 6] = 4
    labels[5][radius < 12] = 2
    labels[5][radius < 8] = 4
    labels[5][(y - 32) ** 2 + (x - 52) ** 2 < 9] = 2
    return SliceCase(images, labels, {"visit_names": VISITS, "spacing_mm": [1.0, 1.0, 1.0]})


def test_domain_blocks_flux_and_conserves_balance():
    initial = np.zeros((20, 20))
    initial[4:8, 4:8] = 0.8
    domain = np.zeros((20, 20), dtype=bool)
    domain[:, :10] = True
    run = simulate_density_2d(initial, 0.5, 0.05, [0, 20], dt_days=0.2, domain=domain)
    assert np.all(run.density[-1][:, 10:] == 0)
    assert run.density[-1][:, :10].sum() > initial.sum()
    assert run.max_balance_residual_mm2 < 1e-9


def test_domain_is_validated():
    initial = np.zeros((5, 5))
    initial[2, 2] = 0.5
    with pytest.raises(ValueError, match="boolean"):
        simulate_density_2d(initial, 0.1, 0.0, [0, 1], domain=np.ones((5, 5)))
    with pytest.raises(ValueError, match="outside the domain"):
        simulate_density_2d(initial, 0.1, 0.0, [0, 1], domain=np.zeros((5, 5), dtype=bool))


def test_literature_conversion_and_front_scales():
    assert lb.LITERATURE["diffusivity_mm2_per_day"] == pytest.approx(0.0814, abs=1e-4)
    assert lb.LITERATURE["rho_per_day"] == pytest.approx(0.0411, abs=1e-4)
    assert lb.front_speed_mm_per_day(0.25, 0.04) == pytest.approx(0.2)
    assert lb.front_width_mm(0.25, 0.04) == pytest.approx(2.5)


def test_component_labels_and_local_distant_split():
    mask = np.zeros((6, 6), dtype=bool)
    mask[0:2, 0:2] = True
    mask[4:6, 4:6] = True
    assert lb.component_labels(mask).max() == 2
    split = lb.local_and_distant(synthetic_case())
    assert split["n_local_components"] == 1 and split["n_distant_components"] == 1
    assert split["distant_core"].sum() == 0 and split["distant_whole"].sum() > 0


def test_two_level_initial_respects_reading_thresholds():
    case = synthetic_case()
    initial = lb.two_level_initial(case)
    assert set(np.unique(initial)) == {0.0, 0.36, 0.9}
    with pytest.raises(ValueError):
        lb.two_level_initial(case, core_level=0.7)
    with pytest.raises(ValueError):
        lb.two_level_initial(case, margin_level=0.1)


def test_run_two_level_scores_and_refuses_perioperative_start():
    case = synthetic_case()
    result = lb.run_two_level(case, diffusivity_mm2_per_day=0.1, rho_per_day=0.1)
    assert result["settings"]["days"] == 28
    assert result["model"]["whole_area_mm2"] > result["no_change"]["whole_area_mm2"]
    assert result["model"]["distant_whole_reached_mm2"] == 0
    assert result["max_balance_residual_mm2"] < 1e-9
    with pytest.raises(ValueError, match="perioperative"):
        lb.run_two_level(case, initial_visit="week-000-2")


def test_calibration_grid_reports_best_cell():
    grid = lb.calibration_grid(synthetic_case(), np.array([0.05, 0.2]), np.array([0.02, 0.1]))
    assert grid["local_score"].shape == (2, 2)
    assert grid["best"]["local_score"] == pytest.approx(grid["local_score"].max())
    summary = lb.identifiability_summary(grid)
    assert summary["score_range_along_D"] >= 0 and summary["score_range_along_rho"] >= 0
