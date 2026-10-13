"""Numerical checks of the 3D proliferation--invasion solver."""

import numpy as np
import pytest

from glioma_ai.growth_model import logistic_solution, simulate_density_2d
from glioma_ai.growth_volume import diffusion_step_limit_3d, simulate_density_3d


def test_uniform_density_follows_the_exact_logistic_curve():
    run = simulate_density_3d(np.full((5, 6, 7), 0.2), 0.3, 0.07, [0, 10])
    np.testing.assert_allclose(run.density[-1], logistic_solution(0.2, 0.07, 10), rtol=1e-6)


def test_pure_diffusion_conserves_mass_inside_a_closed_domain():
    domain = np.zeros((12, 12, 12), dtype=bool)
    domain[2:10, 3:9, 1:11] = True
    initial = np.zeros(domain.shape)
    initial[5, 5, 5] = 1.0
    run = simulate_density_3d(initial, 0.5, 0.0, [0, 5, 20], domain=domain)
    np.testing.assert_allclose(run.integral_mm3, 1.0, rtol=1e-12)
    assert run.density[-1][~domain].max() == 0
    assert run.max_balance_residual_mm3 < 1e-10


def test_symmetric_start_stays_symmetric_under_axis_permutation():
    initial = np.zeros((11, 11, 11))
    initial[4:7, 4:7, 4:7] = 0.8
    final = simulate_density_3d(initial, 0.4, 0.05, [0, 8]).density[-1]
    np.testing.assert_allclose(final, final.transpose(1, 2, 0), atol=1e-6)
    np.testing.assert_allclose(final, final[::-1], atol=1e-6)


def test_density_constant_along_one_axis_reproduces_the_2d_solver():
    plane = np.zeros((9, 10))
    plane[3:6, 4:7] = 0.9
    plane[2, 5] = 0.4
    volume = np.repeat(plane[:, :, None], 4, axis=2)
    three = simulate_density_3d(volume, 0.3, 0.06, [0, 6], dt_days=0.2).density[-1]
    two = simulate_density_2d(plane, 0.3, 0.06, [0, 6], dt_days=0.2).density[-1]
    for k in range(4):
        np.testing.assert_allclose(three[:, :, k], two, atol=1e-6)


def test_stability_bound_and_domain_contract_are_enforced():
    assert diffusion_step_limit_3d(0.5, (1, 1, 1)) == pytest.approx(1 / 3)
    with pytest.raises(ValueError, match="stability"):
        simulate_density_3d(np.zeros((4, 4, 4)), 1.0, 0.0, [0, 1], dt_days=0.2)
    domain = np.ones((4, 4, 4), dtype=bool)
    domain[0] = False
    start = np.zeros((4, 4, 4))
    start[0, 0, 0] = 0.5
    with pytest.raises(ValueError, match="outside the domain"):
        simulate_density_3d(start, 0.1, 0.0, [0, 1], domain=domain)
