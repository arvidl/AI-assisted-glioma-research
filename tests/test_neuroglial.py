"""Analytic limits, unit conversion, observation ambiguity and flux balance."""

import numpy as np
import pytest

from glioma_ai.neuroglial import (
    field_from_potential,
    integrate_potassium,
    potassium_equilibrium_mV,
)


def test_constant_release_matches_independent_continuous_solution_and_flux_balance():
    result = integrate_potassium(np.full(200, 0.6), 0.05, 0.8, 0.1, 0.2)
    time = result["time_s"]
    expected = 0.6 / 0.9 + (0.2 - 0.6 / 0.9) * np.exp(-0.9 * time)
    np.testing.assert_allclose(result["excess_mM"], expected, atol=2e-15)
    total = result["excess_mM"] + result["astro_cleared_mM"] + result["other_cleared_mM"]
    np.testing.assert_allclose(total, 0.2 + result["cumulative_release_mM"], atol=2e-14)
    np.testing.assert_allclose(result["astro_cleared_mM"], 8 * result["other_cleared_mM"])


def test_zero_clearance_accumulates_release_and_no_release_has_exponential_washout():
    result = integrate_potassium(np.array([0, 1, 2]), 0.25, 0, 0, 0.5)
    np.testing.assert_allclose(result["excess_mM"], [0.5, 0.5, 0.75, 1.25])
    np.testing.assert_array_equal(result["astro_cleared_mM"], 0)
    result = integrate_potassium(np.zeros(100), 0.1, 0.8, 0.2, 1)
    np.testing.assert_allclose(result["excess_mM"], np.exp(-result["time_s"]))


def test_release_partition_invariance_and_clearance_confounding():
    direct = integrate_potassium(np.array([0.6, 0.0]), 4, 0.8, 0.1)
    fine = integrate_potassium(np.repeat([0.6, 0.0], 400), 0.01, 0.8, 0.1)
    np.testing.assert_allclose(direct["excess_mM"], fine["excess_mM"][::400], atol=3e-15)
    alternative = integrate_potassium(np.array([0.6, 0.0]), 4, 0.2, 0.7)
    np.testing.assert_allclose(direct["excess_mM"], alternative["excess_mM"], atol=1e-15)
    assert direct["astro_cleared_mM"][-1] > alternative["astro_cleared_mM"][-1]


def test_nernst_voltage_has_correct_sign_zero_and_decade_difference():
    result = potassium_equilibrium_mV(np.array([14, 140]), 140, 37)
    assert result[0] < 0
    assert result[1] == 0
    assert result[1] - result[0] == pytest.approx(61.54, abs=0.02)


def test_field_units_gradient_sign_nonuniform_grid_and_voltage_offset():
    grid = np.array([0.0, 0.1, 0.4, 1.0, 2.0])
    # 1000 microvolts per millimetre = 1 volt per metre.
    potential = 1000 * grid
    np.testing.assert_allclose(field_from_potential(potential, grid), -1, atol=2e-15)
    np.testing.assert_allclose(field_from_potential(potential + 27, grid), -1, atol=2e-15)
    np.testing.assert_allclose(field_from_potential(np.full(5, 200), grid), 0, atol=2e-15)


def test_same_voltage_at_one_position_does_not_identify_field():
    grid = np.linspace(-5, 5, 1001)
    waves = np.array([100 * np.sin(2 * np.pi * grid / w) for w in (10, 2.5)])
    np.testing.assert_allclose(waves[:, 500], 0)
    field = field_from_potential(waves, grid)
    np.testing.assert_allclose(field[1, 500] / field[0, 500], 4, rtol=1e-4)


@pytest.mark.parametrize("bad", [-1, np.nan, np.inf])
def test_negative_or_nonfinite_release_and_rates_are_rejected(bad):
    with pytest.raises(ValueError):
        integrate_potassium(np.array([bad]), 0.1, 0.8, 0.1)
    with pytest.raises(ValueError):
        integrate_potassium(np.ones(3), 0.1, bad, 0.1)


def test_invalid_geometry_temperature_and_steps_are_rejected():
    with pytest.raises(ValueError):
        integrate_potassium(np.ones(3), 0, 0.8, 0.1)
    with pytest.raises(ValueError):
        potassium_equilibrium_mV(np.ones(3), temperature_C=-273.15)
    with pytest.raises(ValueError):
        potassium_equilibrium_mV(np.array([0, 3]))
    with pytest.raises(ValueError):
        field_from_potential(np.ones(3), [0, 1, 1])
    with pytest.raises(ValueError):
        field_from_potential(np.ones(2), [0, 1, 2])
