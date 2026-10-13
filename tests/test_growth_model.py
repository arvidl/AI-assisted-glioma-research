"""Analytic limits, conservation, bounds and convergence of the checked solver."""

import numpy as np
import pytest

from glioma_ai.growth_model import logistic_solution, simulate_density_2d, solver_controls


def test_homogeneous_solution_equals_the_closed_form_at_every_snapshot():
    times = [0, 0.13, 1.7, 8]
    run = simulate_density_2d(np.full((11, 13), 0.2), 0.4, 0.08, times)
    truth = np.array([1 / (1 + 4 * np.exp(-0.08 * t)) for t in times])
    np.testing.assert_allclose(
        run.density,
        np.broadcast_to(truth[:, None, None], run.density.shape),
        rtol=2e-14,
        atol=2e-14,
    )
    assert run.days.tolist() == times
    assert run.max_balance_residual_mm2 < 1e-11


def test_heterogeneous_transport_conserves_mass_and_preserves_extrema():
    rng = np.random.default_rng(10)
    initial = rng.uniform(0.01, 0.99, (17, 19))
    diffusion = rng.uniform(0.1, 0.6, initial.shape)
    run = simulate_density_2d(initial, diffusion, 0, [0, 1, 5], dx_mm=1.3, dy_mm=0.8, dt_days=0.1)
    np.testing.assert_allclose(run.integral_mm2, run.integral_mm2[0], atol=1e-10)
    assert run.density.min() >= initial.min() - 1e-14
    assert run.density.max() <= initial.max() + 1e-14


def test_density_increase_is_accounted_for_by_reaction_not_boundary_flux():
    initial = np.zeros((23, 21))
    initial[8:14, 8:14] = 0.65
    run = simulate_density_2d(initial, 0.4, 0.07, [0, 1, 8])
    np.testing.assert_allclose(
        run.integral_mm2 - run.integral_mm2[0], run.reaction_gain_mm2, atol=1e-10
    )
    assert 0 <= run.density.min() <= run.density.max() <= 1
    assert run.integral_mm2[-1] > run.integral_mm2[0]
    # Thresholding is an observation assumption; the nested sets are guaranteed.
    assert np.all(run.areas_mm2(0.1) >= run.areas_mm2(0.5))


def test_stiff_reaction_has_exact_fixed_points_without_density_clipping():
    result = logistic_solution(np.array([0, 0.1, 0.9, 1]), 100, 100)
    np.testing.assert_array_equal(result, [0, 1, 1, 1])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dt_days": 0.26},
        {"rho_per_day": -1},
        {"days": [0, 1, 1]},
        {"days": [1, 2]},
        {"dx_mm": 0},
        {"diffusivity_mm2_per_day": -1},
        {"initial": np.full((5, 5), 1.1)},
    ],
)
def test_invalid_or_unstable_inputs_are_rejected(kwargs):
    inputs = {
        "initial": np.full((5, 5), 0.2),
        "diffusivity_mm2_per_day": 1,
        "rho_per_day": 0.02,
        "days": [0, 1],
    }
    with pytest.raises(ValueError):
        simulate_density_2d(**{**inputs, **kwargs})


def test_analytic_neumann_mode_error_decreases_under_refinement():
    checked = solver_controls()
    assert checked["homogeneous_logistic_max_error"] < 1e-12
    assert checked["heterogeneous_diffusion_mass_error_mm2"] < 1e-10
    errors = [row["rms_error"] for row in checked["neumann_cosine_refinement"]]
    assert errors[0] / errors[1] > 3.5
    assert errors[1] / errors[2] > 3.5
