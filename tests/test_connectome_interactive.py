import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from glioma_ai.connectome import CASE_DIR, dk82, homotopic_summary, load_case  # noqa: E402
from glioma_ai.connectome_interactive import (  # noqa: E402
    ASSUMED_DOMAINS,
    TUMOUR_CENTRE,
    draw_scenario,
    proxy_calibration,
    resection_scenario,
    segment_distance,
    sphere_resection,
)

needs_case = pytest.mark.skipif(
    not CASE_DIR.is_dir(), reason="tracked sub-PAT16 matrices absent (staged public snapshot)"
)


def test_segment_distance_interior_and_endpoints():
    start = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    end = np.array([[10.0, 0.0, 0.0], [10.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    centre = np.array([5.0, 3.0, 4.0])
    assert np.allclose(segment_distance(start[0], end[0], centre), 5.0)
    beyond = segment_distance(start[1], end[1], np.array([13.0, 4.0, 0.0]))
    assert np.isclose(beyond, 5.0)
    assert np.isclose(segment_distance(start[2], end[2], centre), np.linalg.norm(centre - 1.0))


def test_assumed_domains_name_existing_regions():
    _, names = dk82()
    for keys in ASSUMED_DOMAINS.values():
        for key in keys:
            assert f"L-{key}" in names and f"R-{key}" in names


@needs_case
def test_zero_radius_changes_nothing():
    case = load_case()
    s = resection_scenario(case, "R-insula", 0.0)
    assert not s["removed"].any() and not s["cut"].any()
    assert np.array_equal(s["sc"], case.sc["preop"])
    assert np.allclose(s["strength_percent"], 100) and np.allclose(s["fc_change"], 0)
    assert np.isclose(s["efficiency_percent"], 100)


@needs_case
def test_larger_sphere_removes_at_least_as_much():
    case = load_case()
    centre = case.centroid_mm[case.names.index("R-superiortemporal")]
    previous = sphere_resection(case, centre, 5.0)
    for radius in (10.0, 20.0, 30.0):
        current = sphere_resection(case, centre, radius)
        assert np.all(current["cut"] >= previous["cut"])
        assert np.all(current["sc"] <= previous["sc"])
        previous = current
    assert np.allclose(previous["sc"], previous["sc"].T)
    assert np.all(np.diag(previous["sc"]) == 0)


@needs_case
def test_homotopic_summary_partitions_the_pairs():
    summary = homotopic_summary(load_case())
    for values in summary.values():
        assert values["homotopic"]["pairs"] == 41
        total = sum(values[k]["pairs"] for k in values if k != "interhemispheric_weight_percent")
        assert total == 82 * 81 // 2
        assert 0 <= values["interhemispheric_weight_percent"] <= 100


@needs_case
def test_proxy_calibration_and_drawing():
    case = load_case()
    calibration = proxy_calibration(case)
    for key in ("recall_percent", "precision_percent", "proxy_weight_removed_percent"):
        assert 0 <= calibration[key] <= 100
    expected = 100 * case.sc_tumour[np.triu_indices(82, 1)].sum()
    expected /= case.sc["preop"][np.triu_indices(82, 1)].sum()
    assert np.isclose(calibration["measured_weight_through_mask_percent"], expected)
    figure = plt.figure()
    draw_scenario(figure, case, resection_scenario(case, TUMOUR_CENTRE, 20.0, coupling=0.5))
    plt.close(figure)
