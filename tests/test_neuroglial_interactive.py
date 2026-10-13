"""Teaching helpers and explorer figures for the potassium and field notebooks."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from glioma_ai.neuroglial import (
    integrate_potassium,
    nernst_slope_mV_per_mM,
    potassium_equilibrium_mV,
    single_pulse_excess_mM,
)
from glioma_ai.neuroglial_interactive import (
    clearance_scenario,
    derivative_error_curve,
    draw_clearance_state,
    draw_error_curve,
    draw_sampling_state,
    draw_tumour_border,
    pulse_release,
    sampled_field,
    tumour_border_fields,
)


def test_single_pulse_landmarks_match_the_exact_solver():
    trace = integrate_potassium(np.full(400, 0.6), 0.01, 0.5, 0.25)
    landmarks = single_pulse_excess_mM(0.6, 0.75, 4.0)
    assert trace["excess_mM"][-1] == pytest.approx(landmarks["peak_mM"], rel=1e-13)
    assert landmarks["plateau_mM"] == pytest.approx(0.8)
    assert landmarks["time_constant_s"] == pytest.approx(1 / 0.75)
    assert single_pulse_excess_mM(0.6, 0.0, 4.0)["peak_mM"] == pytest.approx(2.4)


def test_nernst_slope_is_the_derivative_of_the_equilibrium():
    step = 1e-6
    numeric = (potassium_equilibrium_mV(3 + step) - potassium_equilibrium_mV(3 - step)) / (2 * step)
    assert nernst_slope_mV_per_mM(3.0) == pytest.approx(float(numeric), rel=1e-8)
    with pytest.raises(ValueError):
        nernst_slope_mV_per_mM(0)


def test_pulses_and_scenario_balance_and_swap_invariance():
    release = pulse_release(0.6, 4.0, 4.0, 0.01, 30.0)
    assert release.sum() * 0.01 == pytest.approx(0.6 * 8)
    run = clearance_scenario(0.8, 0.1)
    np.testing.assert_allclose(run["excess_mM"], run["swapped_excess_mM"], atol=1e-15)
    accounted = run["excess_mM"] + run["astro_cleared_mM"] + run["other_cleared_mM"]
    np.testing.assert_allclose(accounted, run["cumulative_release_mM"], atol=1e-13)
    assert run["astro_cleared_mM"][-1] > run["swapped_astro_cleared_mM"][-1]
    assert run["equilibrium_shift_mV"].min() >= 0


def test_sampled_field_offset_invariance_and_convergence():
    plain = sampled_field(n_samples=81)
    shifted = sampled_field(n_samples=81, offset_uV=150)
    np.testing.assert_allclose(
        plain["estimated_field_V_per_m"], shifted["estimated_field_V_per_m"], atol=1e-12
    )
    errors = [sampled_field(n_samples=n)["rms_error_V_per_m"] for n in (41, 81, 161)]
    assert errors[0] / errors[1] == pytest.approx(4, rel=0.05)
    assert errors[1] / errors[2] == pytest.approx(4, rel=0.05)
    assert plain["peak_field_V_per_m"] == pytest.approx(100e-6 * 2 * np.pi / 2.5e-3)
    with pytest.raises(ValueError):
        sampled_field(n_samples=2)


def test_error_curve_terms_bracket_the_measured_error():
    noiseless = derivative_error_curve(100, 2.5, 0, np.array([81, 161, 321]), repeats=1)
    np.testing.assert_allclose(
        noiseless["empirical_rms_V_per_m"], noiseless["truncation_rms_V_per_m"], rtol=0.05
    )
    noisy = derivative_error_curve(100, 2.5, 5, np.array([401, 801]), repeats=40)
    np.testing.assert_allclose(noisy["empirical_rms_V_per_m"], noisy["noise_rms_V_per_m"], rtol=0.1)


def test_tumour_border_fields_match_their_analytic_forms():
    run = tumour_border_fields()
    x = run["positions_mm"]
    np.testing.assert_allclose(
        run["activity_numerical_field_V_per_m"], run["activity_field_V_per_m"], atol=1e-4
    )
    assert run["activity_amplitude_uV"][0] == pytest.approx(100, abs=1e-6)
    assert run["activity_amplitude_uV"][-1] == pytest.approx(20, abs=1e-6)
    assert np.abs(run["activity_field_V_per_m"][x < -2]).max() == pytest.approx(
        100e-6 * 2 * np.pi / 2.5e-3, rel=1e-3
    )
    away = np.abs(x) > 0.02
    np.testing.assert_allclose(
        run["step_numerical_field_V_per_m"][away], run["step_field_V_per_m"][away], atol=1e-12
    )
    assert run["parameters"]["field_tumour_V_per_m"] == pytest.approx(0.025)
    assert run["step_potential_uV"][x == 0] == pytest.approx(0)
    for estimate in run["coarse"].values():
        at_border = estimate["estimated_field_V_per_m"][estimate["positions_mm"] == 0]
        assert at_border == pytest.approx(0.0375)
    with pytest.raises(ValueError):
        tumour_border_fields(conductivity_ratio=0)
    with pytest.raises(ValueError):
        tumour_border_fields(border_width_mm=0)


def test_explorer_figures_render():
    figure = plt.figure()
    draw_clearance_state(figure, clearance_scenario(0.2, 0.0))
    figure = plt.figure()
    draw_sampling_state(figure, sampled_field(noise_uV=5))
    figure, axis = plt.subplots()
    draw_error_curve(axis, derivative_error_curve(100, 2.5, 5, np.array([11, 41]), repeats=2), 5)
    figure = plt.figure()
    draw_tumour_border(figure, tumour_border_fields(coarse_spacings_mm=(1.0,)))
    plt.close("all")


def test_figures_render_to_png_and_close():
    from glioma_ai.notebook_display import figure_png

    figure = plt.figure()
    draw_clearance_state(figure, clearance_scenario(0.8, 0.1))
    assert figure_png(figure, dpi=40).startswith(b"\x89PNG")
    assert not plt.fignum_exists(figure.number)
