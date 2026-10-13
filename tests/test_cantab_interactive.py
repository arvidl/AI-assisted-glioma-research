import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from glioma_ai.cantab import METRICS, precision_interval, reliable_change_index
from glioma_ai.cantab_interactive import (
    HYPOTHETICAL_PRESETS,
    change_scenario,
    draw_change_state,
    draw_precision_state,
    measure_table,
    precision_scenario,
)


def test_reliable_change_index_formula_and_edges():
    result = reliable_change_index(5, 6, 1.2, 0.6)
    assert result["standard_error"] == pytest.approx(1.2 * math.sqrt(0.4))
    assert result["s_diff"] == pytest.approx(math.sqrt(2) * 1.2 * math.sqrt(0.4))
    assert result["rci"] == pytest.approx(1 / result["s_diff"])
    assert not result["reliable"]
    assert reliable_change_index(5, 8, 1.2, 0.6)["reliable"]
    for args in ((5, 6, 0, 0.6), (5, 6, 1, 1.0), (5, 6, 1, -0.1), (5, math.nan, 1, 0.5)):
        with pytest.raises(ValueError):
            reliable_change_index(*args)


def test_precision_interval_matches_agreement():
    interval = precision_interval("0.70")
    assert interval["quantum"] == pytest.approx(0.01)
    assert (interval["low"], interval["high"]) == pytest.approx((0.695, 0.705))
    assert precision_scenario("0.70", "0.702")["verdict"] == "at_release_precision"
    assert precision_scenario("0.70", "0.72")["verdict"] == "mismatch"
    assert precision_interval("12")["quantum"] == 1


def test_direction_follows_measure_sense():
    faster = change_scenario(
        "RTI_fiveRT", baseline=400, follow_up=250, baseline_sd=40, reliability=0.8
    )
    assert faster["reading"] == "reliable improvement"
    slower = change_scenario(
        "RTI_fiveRT", baseline=250, follow_up=400, baseline_sd=40, reliability=0.8
    )
    assert slower["reading"] == "reliable decline"
    assert change_scenario()["reading"] == "within measurement error"


def test_tables_and_presets_cover_every_measure():
    assert {row["code"] for row in measure_table()} == set(METRICS)
    assert set(HYPOTHETICAL_PRESETS) == set(METRICS)
    for preset in HYPOTHETICAL_PRESETS.values():
        low, high, _ = preset["score"]
        assert low <= preset["baseline"] <= high and low <= preset["follow_up"] <= high


def test_cantab_figures_render():
    figure, axis = plt.subplots()
    draw_precision_state(axis, precision_scenario())
    plt.close(figure)
    figure = plt.figure()
    draw_change_state(figure, change_scenario())
    assert len(figure.axes) == 2
    plt.close(figure)
