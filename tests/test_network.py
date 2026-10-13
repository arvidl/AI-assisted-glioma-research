"""Constructed phantom network: geometry, damage rules, linear dynamics and figures."""

import json
from functools import lru_cache

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from glioma_ai.growth_interactive import _cached_tissue
from glioma_ai.network import (
    COGNITIVE_ASSUMPTIONS,
    callosum_sparing,
    domain_strength,
    lesion_course,
    linear_controls,
    linear_fc,
    network_summary,
    phantom_network,
    resection_cavity,
    resection_state,
    spectral_radius,
    tract_integrity,
)
from glioma_ai.network_figures import (
    DEFAULT_GROWTH,
    draw_network_state,
    draw_resection,
    write_network_experiment,
)
from glioma_ai.tissue_growth import CSF, GREY, LEFT_RIGHT


@lru_cache(maxsize=1)
def setting():
    phantom, runs, _ = _cached_tissue(*DEFAULT_GROWTH)
    return phantom, runs, phantom_network(phantom)


def test_regions_paths_and_weights():
    phantom, _, network = setting()
    assert network.size == 14
    for k in range(network.size):
        cells = np.argwhere(network.labels == k)
        assert len(cells) > 50
        x = phantom.x_mm[cells[:, 0]]
        assert np.all(x < 0) if network.hemisphere[k] == "R" else np.all(x > 0)
    assert np.isfinite(network.length_mm[~np.eye(14, dtype=bool)]).all()
    w = network.weight
    assert np.allclose(w, w.T) and np.all(np.diag(w) == 0)
    assert np.all((w[~np.eye(14, dtype=bool)] > 0) & (w[~np.eye(14, dtype=bool)] < 1))
    for i in range(14):
        for j in range(i + 1, 14):
            path = network.paths[i][j]
            inner = tuple(path[1:-1].T)
            assert not np.any(phantom.tissue[inner] == CSF)
            assert not np.any(phantom.tissue[inner] == GREY)
            if network.interhemispheric[i, j]:
                assert np.any(phantom.fibre[tuple(path.T)] == LEFT_RIGHT)


@pytest.mark.parametrize("rule", ["attenuation", "max"])
def test_integrity_is_one_without_tumour_and_never_increases_with_density(rule):
    phantom, runs, network = setting()
    assert np.all(tract_integrity(network, np.zeros(phantom.tissue.shape), rule=rule) == 1)
    for density in runs[list(runs)[-1]][0].density[::12]:
        larger = np.minimum(1.0, 1.2 * density + 0.05 * phantom.brain)
        lower, higher = (tract_integrity(network, c, rule=rule) for c in (larger, density))
        assert np.all(lower <= higher + 1e-12) and lower.min() >= 0
    with pytest.raises(ValueError):
        tract_integrity(network, np.full(phantom.tissue.shape, 1.5))


def test_lesions_cannot_raise_spectral_radius_or_interhemispheric_weight():
    phantom, runs, network = setting()
    run = runs[list(runs)[-1]][0]
    course = lesion_course(phantom, network, run)
    assert np.all(course["radius"] <= 1 + 1e-12)
    assert course["inter_sc"][0] == 1 and course["inter_sc"][-1] < 0.5
    spared = lesion_course(phantom, network, run, spare_callosum=True)
    assert np.all(spared["inter_sc"] >= course["inter_sc"] - 1e-12)
    assert spared["inter_sc"][-1] > course["inter_sc"][-1]


def test_linear_fc_is_exact_and_rejects_instability():
    _, _, network = setting()
    w = network.weight / spectral_radius(network.weight)
    _, uncoupled = linear_fc(w, coupling=0.0)
    assert np.allclose(uncoupled, np.eye(14))
    covariance, correlation = linear_fc(w, coupling=0.8)
    a = 0.8 * w - np.eye(14)
    assert np.abs(a @ covariance + covariance @ a.T + np.eye(14)).max() < 1e-12
    assert np.allclose(np.diag(correlation), 1)
    with pytest.raises(ValueError):
        linear_fc(w, coupling=1.05)


def test_simulation_controls_separate_step_bias_and_sampling_error():
    _, _, network = setting()
    controls = linear_controls(network.weight / spectral_radius(network.weight))
    bias = [row["max_abs_difference"] for row in controls["step_bias"]]
    assert all(0.4 < later / earlier < 0.6 for earlier, later in zip(bias, bias[1:], strict=False))
    sampling = [row["rms_error"] for row in controls["sampling"]]
    assert sampling[-1] < sampling[0] / 1.5
    assert controls["lyapunov_residual_max"] < 1e-12


def test_resection_spares_callosum_grey_matter_and_other_hemisphere():
    phantom, runs, network = setting()
    density = runs[list(runs)[-1]][0].density[24]
    cavity = resection_cavity(phantom, density)
    assert cavity.any()
    assert not np.any(phantom.fibre[cavity] == LEFT_RIGHT)
    assert not np.any(phantom.tissue[cavity] == GREY)
    assert np.all(phantom.x_mm[np.nonzero(cavity)[0]] > 0)
    state = resection_state(phantom, network, density)
    totals = {name: s["total_weight"] for name, s in state["summaries"].items()}
    assert totals["healthy"] > totals["pre-operative"] > totals["post-operative"]
    sparing = callosum_sparing(phantom, density)
    assert np.all(sparing[phantom.fibre == LEFT_RIGHT] == 0)


def test_assumed_domains_mark_missing_frontal_regions():
    _, _, network = setting()
    healthy = domain_strength(network, network.weight)
    assert healthy["SOC planning"] is None and COGNITIVE_ASSUMPTIONS["SOC planning"] == ()
    assert all(v == {"L": 1.0, "R": 1.0} for v in healthy.values() if v is not None)
    assert network_summary(network, network.weight)["global_efficiency"] > 0


def test_figures_render_and_record_is_written(tmp_path):
    phantom, runs, network = setting()
    figure = plt.figure(figsize=(12, 4))
    draw_network_state(figure, phantom, network, runs, 180)
    plt.close(figure)
    density = runs[list(runs)[-1]][0].density[24]
    figure = plt.figure(figsize=(12, 4))
    draw_resection(figure, phantom, network, resection_state(phantom, network, density), 120)
    plt.close(figure)
    record = write_network_experiment(tmp_path)
    saved = json.loads((tmp_path / "network_experiment.json").read_text())
    assert saved["evidence_type"] == "synthetic_construction" == record["evidence_type"]
    assert (tmp_path / "network_lesion.png").is_file()
    assert (tmp_path / "network_resection.pdf").is_file()
