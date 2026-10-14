import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from glioma_ai import lumiere_biology
from glioma_ai.tumour_interface import (
    DIFFUSIVITIES_MM2_PER_YEAR,
    RHO_PER_YEAR,
    T1GD_FRACTION,
    T2_FRACTION,
    draw_iceberg,
    iceberg_profiles,
)


@pytest.fixture(scope="module")
def run():
    return iceberg_profiles()


def test_reading_levels_and_coefficients_match_notebook_03():
    assert T1GD_FRACTION == lumiere_biology.T1GD_FRACTION
    assert T2_FRACTION == lumiere_biology.T2_FRACTION
    literature = lumiere_biology.LITERATURE
    assert DIFFUSIVITIES_MM2_PER_YEAR["median"] / 365 == pytest.approx(
        literature["diffusivity_mm2_per_day"]
    )
    assert RHO_PER_YEAR / 365 == pytest.approx(literature["rho_per_day"])


def test_every_case_stops_with_its_t1gd_boundary_at_the_radius(run):
    for case in run["cases"].values():
        assert 15.0 <= case["extent_mm"]["T1Gd"] < 15.2
        extents = case["extent_mm"]
        assert extents["T1Gd"] < extents["T2/FLAIR"] < extents["1%"]
        assert case["front_width_mm"] == pytest.approx(
            np.sqrt(case["diffusivity_mm2_per_year"] / RHO_PER_YEAR)
        )


def test_more_diffusive_tumours_hide_more_cells_beyond_the_visible_boundaries(run):
    cases = [run["cases"][name] for name in ("nodular", "median", "diffuse")]
    margins = [case["invisible_margin_mm"] for case in cases]
    beyond = [case["fraction_beyond_margin"] for case in cases]
    assert margins == sorted(margins)
    assert beyond == sorted(beyond)
    assert beyond[0] == 0.0
    assert beyond[2] > 0.2


def test_region_shares_sum_to_one_and_hits_follow_the_extents(run):
    for case in run["cases"].values():
        shares = sum(region["cell_share"] for region in case["regions"].values())
        assert shares == pytest.approx(1.0, abs=1e-3)
        for region in case["regions"].values():
            assert region["T1Gd"] <= region["T2/FLAIR"] <= region["1%"]
    assert run["cases"]["nodular"]["regions"]["B"]["1%"] == 0.0
    assert run["cases"]["diffuse"]["regions"]["C"]["T2/FLAIR"] > 0.0


def test_grid_refinement_does_not_change_the_boundaries(run):
    fine = iceberg_profiles(dx_mm=0.05)
    for name, case in run["cases"].items():
        for label, extent in case["extent_mm"].items():
            assert fine["cases"][name]["extent_mm"][label] == pytest.approx(extent, abs=0.3)


def test_invalid_parameters_are_rejected():
    with pytest.raises(ValueError):
        iceberg_profiles({"bad": 0.0})
    with pytest.raises(ValueError):
        iceberg_profiles(t1gd_radius_mm=0.5)
    with pytest.raises(ValueError):
        iceberg_profiles({"wide": 468.9}, span_mm=20.0)


def test_figure_draws_two_panels(run):
    figure = plt.figure()
    draw_iceberg(figure, run)
    assert len(figure.axes) == 2
    plt.close(figure)
