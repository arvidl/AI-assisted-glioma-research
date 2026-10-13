"""The synthetic reaction-diffusion example keeps its prescribed assumptions."""

import numpy as np
import pytest

from glioma_ai.growth import (
    fisher_step,
    fisher_step_2d,
    integrate_fisher_2d,
    spatiotemporal_specification,
    synthetic_directed_infiltration,
)


def test_directed_diffusivity_moves_the_low_density_front():
    result = synthetic_directed_infiltration()
    visible = result["isotropic_visible"]
    low = result["isotropic_infiltrative"]
    assert visible["left"] == visible["right"]
    assert low["left"] == low["right"]
    assert low["right"] > visible["right"]
    directed = result["directed_infiltrative"]
    assert directed["right"] > directed["left"] == low["left"]
    assert result["directed_visible"]["right"] > result["directed_visible"]["left"]
    assert np.all((result["directed"] >= -1e-10) & (result["directed"] <= 1 + 1e-10))


def test_specification_prescribes_the_solver_and_skips_inference():
    record = spatiotemporal_specification()
    assert record["solver"] == "explicit finite difference"
    assert record["inverse_estimation"] == "not_performed"
    assert record["recurrence_prediction"] == "not_performed"
    assert record["patient_images"] == "none"
    solved = synthetic_directed_infiltration()
    assert solved["specification"] == record


def test_explicit_step_rejects_an_unstable_time_step():
    with pytest.raises(ValueError, match="stability"):
        fisher_step(np.ones(5), np.full(5, 1.0), 0.0, dx=1.0, dt=1.0)


def test_plane_step_conserves_mass_when_proliferation_is_zero():
    rng = np.random.default_rng(0)
    initial = rng.random((8, 9))
    solved = integrate_fisher_2d(initial, 0.2, 0.0, dx=1.0, dy=1.0, dt=0.2, n_steps=5)
    assert solved.sum() == pytest.approx(initial.sum())
    assert solved.min() >= -1e-12
    assert solved.max() <= 1 + 1e-12


def test_zero_diffusivity_leaves_a_binary_indicator_unchanged():
    indicator = np.zeros((6, 6))
    indicator[2:4, 2:4] = 1.0
    solved = integrate_fisher_2d(indicator, 0.0, 0.05, dx=1.0, dy=1.0, dt=0.2, n_steps=10)
    assert np.allclose(solved, indicator)


def test_plane_step_rejects_an_unstable_time_step():
    with pytest.raises(ValueError, match="stability"):
        fisher_step_2d(np.ones((4, 4)), 1.0, 0.0, dx=1.0, dy=1.0, dt=1.0)


def test_higher_diffusivity_on_the_right_moves_mass_that_way():
    plane = np.zeros((21, 21))
    plane[10, 10] = 1.0
    diffusion = np.full(plane.shape, 0.05)
    diffusion[:, 11:] = 0.40
    solved = integrate_fisher_2d(plane, diffusion, 0.0, dx=1.0, dy=1.0, dt=0.2, n_steps=30)
    assert solved[:, 11:].sum() > solved[:, :10].sum()
