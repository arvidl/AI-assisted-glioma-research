"""Phantom geometry, tissue-guided solver checks and the notebook 02 drawing helpers."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from glioma_ai.growth_interactive import disk_run, draw_disk_state, draw_tissue_state
from glioma_ai.tissue_growth import (
    CSF,
    GREY,
    LEFT_RIGHT,
    WHITE,
    anisotropic_step_limit,
    contralateral_summary,
    coronal_phantom,
    simulate_tissue_density_2d,
    tissue_fields,
    tissue_scenarios,
    tissue_solver_controls,
    tumour_seed,
)


@pytest.fixture(scope="module")
def phantom():
    return coronal_phantom()


@pytest.fixture(scope="module")
def short_runs(phantom):
    return tissue_scenarios(phantom, days=np.arange(0, 241, 40, dtype=float))


def test_hemispheres_connect_only_through_left_right_callosal_fibres(phantom):
    midline = np.abs(phantom.x_mm) <= 1.5
    tissue, fibre = phantom.tissue[midline], phantom.fibre[midline]
    assert np.all((tissue == CSF) | (tissue == 0) | (fibre == LEFT_RIGHT))
    assert (fibre == LEFT_RIGHT).any()
    assert {CSF, GREY, WHITE} <= set(np.unique(phantom.tissue))


def test_seed_is_left_parietal_white_matter_in_radiological_coordinates(phantom):
    seed = tumour_seed(phantom)
    x, y = np.meshgrid(phantom.x_mm, phantom.y_mm, indexing="ij")
    assert seed.max() == 0.65
    assert np.all(phantom.tissue[seed > 0] == WHITE)
    assert x[seed > 0].min() > 30 and y[seed > 0].min() > 20


def test_tissue_fields_block_csf_and_scale_only_the_fibre_direction(phantom):
    d_xx, d_yy, rho = tissue_fields(phantom, 0.1, 5, 3, 0.04)
    csf = phantom.tissue == CSF
    assert np.all(d_xx[csf] == 0) and np.all(d_yy[csf] == 0) and np.all(rho[csf] == 0)
    callosal = phantom.fibre == LEFT_RIGHT
    np.testing.assert_allclose(d_xx[callosal], 1.5)
    np.testing.assert_allclose(d_yy[callosal], 0.5)
    np.testing.assert_allclose(d_xx[phantom.tissue == GREY], 0.1)
    with pytest.raises(ValueError):
        tissue_fields(phantom, 0.1, 0.5, 1, 0.04)


def test_tissue_solver_reduces_conserves_blocks_and_converges():
    checks = tissue_solver_controls()
    assert checks["isotropic_reduction_max_difference"] < 1e-13
    assert checks["barrier_cells_max_density"] == 0
    assert checks["barrier_side_mass_change"] < 1e-10
    assert checks["heterogeneous_anisotropic_mass_error_mm2"] < 1e-10
    errors = [row["rms_error"] for row in checks["anisotropic_cosine_refinement"]]
    assert errors[0] / errors[1] > 3.5 and errors[1] / errors[2] > 3.5


def test_axis_aligned_anisotropy_spreads_further_along_the_faster_axis():
    initial = np.zeros((41, 41))
    initial[18:23, 18:23] = 0.6
    run = simulate_tissue_density_2d(
        initial, np.full(initial.shape, 0.8), np.full(initial.shape, 0.2), 0.0, [0, 10]
    )
    offset = np.arange(41) - 20.0
    final = run.density[-1]
    assert (final * offset[:, None] ** 2).sum() > 2 * (final * offset[None, :] ** 2).sum()


def test_steps_above_the_positivity_limit_are_rejected():
    d = np.full((7, 7), 1.0)
    limit = anisotropic_step_limit(d, d)
    assert limit == pytest.approx(0.25)
    with pytest.raises(ValueError):
        simulate_tissue_density_2d(np.full((7, 7), 0.2), d, d, 0.0, [0, 1], dt_days=0.3)


def test_tissue_effects_increase_contralateral_spread(phantom, short_runs):
    shares = [
        contralateral_summary(phantom, run)["contralateral_fraction"][-1]
        for run, _ in short_runs.values()
    ]
    assert shares[0] < shares[1] < shares[2]
    for run, _ in short_runs.values():
        assert run.max_balance_residual_mm2 < 1e-9
        assert 0 <= run.density.min() <= run.density.max() <= 1


def test_controls_animation_plays_every_run_and_frame():
    from glioma_ai.growth_examples import controls_animation

    coordinates = np.arange(21, dtype=float) - 10
    days = np.array([0.0, 1.0, 2.0])
    runs = {name: np.full((3, 21, 21), 0.1 * (k + 1)) for k, name in enumerate("ABC")}
    html = controls_animation(runs, days, coordinates, half_width_mm=8)
    assert "<script" in html and html.count("data:image/png;base64") == 3


def test_explorer_day_slider_gets_a_linked_play_button():
    widgets = pytest.importorskip("ipywidgets")
    from glioma_ai.growth_interactive import _with_player

    controls = {
        "d": widgets.FloatSlider(0.3, min=0, max=1),
        "day": widgets.IntSlider(10, min=0, max=40, step=2),
    }
    box = _with_player(widgets, controls, lambda d, day: None, interval_ms=500)
    row = box.children[0].children[1]
    player = row.children[1]
    assert isinstance(player, widgets.Play)
    assert (player.min, player.max, player.step, player.value) == (0, 40, 2, 10)


def test_drawing_helpers_render_without_widgets(phantom, short_runs):
    figure = plt.figure()
    draw_disk_state(figure, disk_run(0.35, 0.035), 28, 0.5, 0.35, 0.035)
    plt.close(figure)
    figure = plt.figure()
    draw_tissue_state(figure, phantom, short_runs, 200)
    plt.close(figure)
