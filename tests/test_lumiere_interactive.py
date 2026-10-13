import matplotlib.pyplot as plt
import numpy as np
import pytest
from test_lumiere_biology import synthetic_case

from glioma_ai import lumiere_biology as bio
from glioma_ai import lumiere_interactive as li


def test_shift_mask_grows_and_shrinks():
    mask = np.zeros((9, 9), dtype=bool)
    mask[3:6, 3:6] = True
    assert li.shift_mask(mask, 1).sum() == 9 + 12
    assert li.shift_mask(mask, -1).sum() == 1
    assert np.array_equal(li.shift_mask(mask, 0), mask)


def test_defaults_reproduce_section_8_at_day_28():
    case = synthetic_case()
    reference = bio.run_two_level(case)["model"]
    result = li.what_if_run(case)
    assert result["at_observed_day"] == pytest.approx(reference)
    assert result["run"].days[-1] == li.HORIZON_DAYS


def test_what_if_settings_change_the_run_and_are_validated():
    case = synthetic_case()
    base = li.what_if_run(case)
    faster = li.what_if_run(case, abnormal_factor=4.0, diffusivity_mm2_per_day=1.0)
    assert faster["time_step_days"] < 0.2
    assert faster["run"].max_balance_residual_mm2 < 1e-8
    assert not np.allclose(base["t2_area_mm2"], faster["t2_area_mm2"])
    grown = li.what_if_run(case, boundary_shift_mm=2)
    assert grown["run"].density[0].astype(bool).sum() > base["run"].density[0].astype(bool).sum()
    assert li.check_settings({**li.DEFAULTS, "margin_level": 0.9}) is not None
    with pytest.raises(ValueError):
        li.what_if_run(case, core_threshold=0.1)


def test_draw_what_if_renders_observed_and_projected_days():
    case = synthetic_case()
    result = li.what_if_run(case)
    for day in (li.OBSERVED_DAY, 84):
        figure = plt.figure()
        li.draw_what_if(figure, case, result, day)
        plt.close(figure)


def test_explorer_builds_with_widgets():
    pytest.importorskip("ipywidgets")
    li.what_if_explorer(synthetic_case())
