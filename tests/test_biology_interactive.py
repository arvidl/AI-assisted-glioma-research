import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from glioma_ai.biology import NeuronGliomaParameters, niche_transition, well_mixed_neuron_glioma
from glioma_ai.biology_interactive import (
    draw_feedback_state,
    draw_niche_state,
    draw_spatial_state,
    draw_well_mixed,
    feedback_scenario,
    logistic_density,
    niche_landmarks,
    niche_scenario,
    signal_nullcline,
    spatial_scenario,
    well_mixed_fraction,
    well_mixed_scenario,
)


def test_well_mixed_limits_match_exact_solutions():
    params = NeuronGliomaParameters(signal_growth_coupling=0, tumor_signal_feedback_per_day=0)
    run = well_mixed_neuron_glioma(0.05, 0.9, 0.3, params, 0.5, 300)
    np.testing.assert_allclose(
        run["density"], logistic_density(0.05, 0.04, run["time_days"]), rtol=1e-9
    )
    # RK4 truncation with dt/tau = 0.125 is about 5e-7.
    np.testing.assert_allclose(run["signal"], 0.3 + 0.6 * np.exp(-run["time_days"] / 4), atol=2e-6)


def test_well_mixed_is_fourth_order():
    params = NeuronGliomaParameters()

    def final(dt):
        return well_mixed_neuron_glioma(0.05, 0.3, 0.3, params, dt, int(round(60 / dt)))

    reference = final(0.01)
    errors = [abs(final(dt)["density"][-1] - reference["density"][-1]) for dt in (2.0, 1.0)]
    assert errors[0] / errors[1] == pytest.approx(16, rel=0.15)


def test_one_way_equals_effective_logistic_and_feedback_raises_signal():
    run = feedback_scenario()
    one_way = run["runs"]["one_way"]
    np.testing.assert_allclose(one_way["density"], run["effective_logistic"], rtol=1e-8)
    np.testing.assert_allclose(one_way["signal"], 0.3, atol=1e-14)
    feedback = run["runs"]["feedback"]
    assert feedback["signal"][-1] > 0.3
    assert feedback["density"][-1] > one_way["density"][-1]
    expected = signal_nullcline(feedback["density"][-1], 0.3, 0.12, 4.0)
    assert feedback["signal"][-1] == pytest.approx(expected, abs=0.01)


def test_niche_closed_form_matches_package_and_identifiability():
    days = np.array([0.0, 5.0, 30.0])
    for day, expected in zip(days, well_mixed_fraction(0.08, 0.02, 0.6, days, 0.1), strict=True):
        _, mes = niche_transition(
            np.full((3, 3), 0.63), np.full((3, 3), 0.07), np.full((3, 3), 0.6), 0.08, 0.02, day
        )
        assert mes[0, 0] / 0.7 == pytest.approx(expected, rel=1e-12)
    marks = niche_landmarks(0.08, 0.02, 1.0)
    assert marks["equilibrium_fraction"] == pytest.approx(0.8)
    assert marks["time_constant_days"] == pytest.approx(10)
    run = well_mixed_scenario(rate_scale=2.0)
    assert run["scaled_landmarks"]["equilibrium_fraction"] == pytest.approx(0.8)
    assert run["scaled_landmarks"]["time_constant_days"] == pytest.approx(5)
    assert run["fraction"][-1] == pytest.approx(run["scaled_fraction"][-1], abs=1e-3)
    assert not np.allclose(run["fraction"][20:60], run["scaled_fraction"][20:60])


def test_niche_scenario_conserves_total_and_responds_to_cue():
    run = niche_scenario()
    assert run["total_change_max_abs"] < 1e-15
    assert run["overall"][-1] > run["overall_no_cue"][-1]
    assert run["overall"][-1] < run["long_run_overall"] + 1e-12
    far = niche_scenario(cue_x_mm=20.0)
    assert far["overall"][-1] < run["overall"][-1]


def test_spatial_scenario_orders_cases():
    run = spatial_scenario(day=10.0)
    final = {key: value["density_integral_mm2"][-1] for key, value in run["runs"].items()}
    assert final["feedback"] > final["one_way"] > final["baseline"]
    with pytest.raises(ValueError):
        spatial_scenario(drive_amplitude=0.95)


def test_biology_figures_render():
    for draw, run in (
        (draw_well_mixed, well_mixed_scenario()),
        (draw_niche_state, niche_scenario()),
        (draw_feedback_state, feedback_scenario(horizon_days=20)),
        (draw_spatial_state, spatial_scenario(day=2.0)),
    ):
        figure = plt.figure()
        draw(figure, run)
        assert len(figure.axes) >= 2
        plt.close(figure)
