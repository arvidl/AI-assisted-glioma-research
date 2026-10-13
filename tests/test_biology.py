"""Independent limits, conservation, analytic solutions, and controlled contrasts."""

from dataclasses import replace

import numpy as np
import pytest

from glioma_ai.biology import (
    NeuronGliomaParameters,
    neuron_glioma_step,
    neuron_glioma_step_limit,
    niche_transition,
    simulate_neuron_glioma,
)
from glioma_ai.growth import integrate_fisher_2d


def test_niche_conserves_local_abundance_and_has_analytic_equilibrium():
    other, mes, cue = np.full((4, 5), 0.7), np.full((4, 5), 0.1), np.ones((4, 5))
    p, q = niche_transition(other, mes, cue, 0.08, 0.02, 10_000)
    np.testing.assert_allclose(p + q, other + mes, rtol=0, atol=1e-15)
    np.testing.assert_allclose(q, 0.8 * 0.08 / 0.10)
    unchanged = niche_transition(other, mes, cue, 0, 0, 10)
    np.testing.assert_allclose(unchanged[0], other, rtol=0, atol=1e-15)
    np.testing.assert_allclose(unchanged[1], mes, rtol=0, atol=1e-15)


def test_niche_exact_solution_is_independent_of_time_partition():
    rng = np.random.default_rng(17)
    total, signal = rng.uniform(0.2, 0.9, (5, 6)), rng.uniform(0, 1, (5, 6))
    direct = niche_transition(0.9 * total, 0.1 * total, signal, 0.08, 0.02, 10)
    first = niche_transition(0.9 * total, 0.1 * total, signal, 0.08, 0.02, 3)
    split = niche_transition(*first, signal, 0.08, 0.02, 7)
    for a, b in zip(direct, split, strict=True):
        np.testing.assert_allclose(a, b, atol=1e-15)


def test_zero_signal_has_only_prescribed_reverse_transition():
    other, mes = np.full((4, 4), 0.6), np.full((4, 4), 0.2)
    p, q = niche_transition(other, mes, np.zeros((4, 4)), 0.8, 0.02, 10)
    np.testing.assert_allclose(q, 0.2 * np.exp(-0.02 * 10))
    np.testing.assert_allclose(p + q, 0.8)


def test_uncoupled_density_is_identical_to_existing_fisher_baseline():
    rng = np.random.default_rng(12)
    cells, activity = rng.uniform(0, 0.7, (9, 11)), rng.uniform(0, 1, (9, 11))
    params = NeuronGliomaParameters(signal_growth_coupling=0)
    result = simulate_neuron_glioma(cells, activity, activity, params, 1, 1, 0.1, 20)
    baseline = integrate_fisher_2d(cells, 0.2, 0.04, 1, 1, 0.1, 20)
    np.testing.assert_array_equal(result["density"], baseline)


def test_no_reaction_conserves_density_integral_even_with_feedback():
    rng = np.random.default_rng(7)
    cells = rng.uniform(0, 0.8, (8, 9))
    drive = np.full_like(cells, 0.3)
    result = simulate_neuron_glioma(
        cells, drive, drive, NeuronGliomaParameters(proliferation_per_day=0), 1, 2, 0.1, 80
    )
    np.testing.assert_allclose(result["density_integral_mm2"], cells.sum() * 2, rtol=1e-13)


def test_constant_signal_logistic_solution_converges_when_step_halves():
    params = NeuronGliomaParameters(diffusivity_mm2_per_day=0, tumor_signal_feedback_per_day=0)
    cells, activity = np.full((3, 3), 0.2), np.full((3, 3), 0.4)
    rate, elapsed = 0.04 * (1 + 1.5 * 0.4), 10
    exact = 1 / (1 + 4 * np.exp(-rate * elapsed))
    coarse = simulate_neuron_glioma(cells, activity, activity, params, 1, 1, 0.1, 100)
    fine = simulate_neuron_glioma(cells, activity, activity, params, 1, 1, 0.05, 200)
    error_coarse = abs(coarse["density"][0, 0] - exact)
    error_fine = abs(fine["density"][0, 0] - exact)
    assert error_fine < 0.55 * error_coarse
    np.testing.assert_array_equal(fine["signal"], activity)


def test_combined_step_bound_preserves_states_without_clipping():
    rng = np.random.default_rng(21)
    cells, drive = rng.uniform(0, 1, (8, 9)), rng.uniform(0, 1, (8, 9))
    params = NeuronGliomaParameters(signal_growth_coupling=5, tumor_signal_feedback_per_day=2)
    dt = 0.99 * neuron_glioma_step_limit(params, 1, 1)
    result = simulate_neuron_glioma(cells, drive, drive, params, 1, 1, dt, 50)
    for key in ("density", "signal"):
        assert result[key].min() >= 0
        assert result[key].max() <= 1
    with pytest.raises(ValueError, match="bound"):
        neuron_glioma_step(cells, drive, drive, params, 1, 1, 1.01 * dt / 0.99)


def test_feedback_changes_signal_and_growth_when_growth_is_coupled():
    cells, drive = np.full((3, 3), 0.2), np.full((3, 3), 0.3)
    params = NeuronGliomaParameters()
    one_way = simulate_neuron_glioma(
        cells, drive, drive, replace(params, tumor_signal_feedback_per_day=0), 1, 1, 0.1, 100
    )
    feedback = simulate_neuron_glioma(cells, drive, drive, params, 1, 1, 0.1, 100)
    assert feedback["density"].sum() > one_way["density"].sum()
    assert feedback["signal"].mean() > one_way["signal"].mean()


def test_constant_signal_growth_is_confounded_with_basal_proliferation():
    cells, drive = np.full((4, 5), 0.2), np.full((4, 5), 0.3)
    params = NeuronGliomaParameters(tumor_signal_feedback_per_day=0)
    coupled = simulate_neuron_glioma(cells, drive, drive, params, 1, 1, 0.1, 100)
    effective = replace(
        params, signal_growth_coupling=0, proliferation_per_day=0.04 * (1 + 1.5 * 0.3)
    )
    alternative = simulate_neuron_glioma(cells, drive, drive, effective, 1, 1, 0.1, 100)
    np.testing.assert_allclose(coupled["density"], alternative["density"], rtol=1e-13)


@pytest.mark.parametrize("bad", [-0.1, 1.1, np.nan, np.inf])
def test_signal_indices_cannot_be_silently_clipped_or_reinterpreted(bad):
    cells = np.full((3, 3), 0.2)
    signal = np.full((3, 3), bad)
    with pytest.raises(ValueError, match="between"):
        niche_transition(cells, cells, signal, 0.08, 0.02, 10)
    with pytest.raises(ValueError, match="between"):
        neuron_glioma_step(cells, signal, cells, NeuronGliomaParameters(), 1, 1, 0.1)


def test_grid_rates_and_step_count_are_explicit():
    cells = np.full((3, 3), 0.2)
    with pytest.raises(ValueError, match="grid"):
        niche_transition(cells, cells, np.ones((3, 4)), 0.08, 0.02, 10)
    with pytest.raises(ValueError, match="nonnegative"):
        niche_transition(cells, cells, cells, -0.08, 0.02, 10)
    with pytest.raises(ValueError, match="relaxation"):
        NeuronGliomaParameters(signal_relaxation_days=0)
    with pytest.raises(ValueError, match="integer"):
        simulate_neuron_glioma(cells, cells, cells, NeuronGliomaParameters(), 1, 1, 0.1, 2.5)
