"""The Patient-048 slice keeps its grid, labels, and prescribed step."""

import json
from pathlib import Path

import numpy as np
import pytest

from glioma_ai.lumiere_slice import (
    compartment_areas_mm2,
    component_coverage,
    illustrate_patient048,
    largest_uncovered_mask,
    lumiere_p048_root,
    min_distance_mm,
    select_axial_index,
    slice_specification,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_axial_index_prefers_the_plane_present_at_every_visit():
    quiet = np.zeros((4, 4, 3), dtype=np.int16)
    shared = quiet.copy()
    shared[1, 1, 1] = 1
    broad = quiet.copy()
    broad[:, :, 0] = 2
    broad[1, 1, 1] = 4
    assert select_axial_index([shared, broad]) == 1


def test_component_coverage_reports_a_missed_region():
    reference = np.zeros((8, 8), dtype=bool)
    reference[1:3, 1:3] = True
    reference[5:7, 5:7] = True
    prediction = np.zeros_like(reference)
    prediction[1:3, 1:3] = True
    coverage = component_coverage(reference, prediction)
    assert coverage == [(4, 4), (4, 0)]


def test_uncovered_component_keeps_its_stored_labels_and_distance():
    labels = np.zeros((8, 8), dtype=np.int16)
    labels[1:3, 1:3] = 4
    labels[5:7, 5:7] = 2
    reference = np.isin(labels, (1, 2, 4))
    prediction = np.zeros_like(reference)
    prediction[1:3, 1:3] = True
    missed = largest_uncovered_mask(reference, prediction)
    assert compartment_areas_mm2(np.where(missed, labels, 0)) == {
        "necrosis_or_non_enhancing": 0,
        "edema": 4,
        "enhancing_tumor": 0,
    }
    assert min_distance_mm(missed, prediction) == pytest.approx(np.hypot(5 - 2, 5 - 2))


def test_slice_specification_does_not_fit_or_cross_resection():
    record = slice_specification()
    assert record["solver"] == "explicit finite difference"
    assert record["inverse_estimation"] == "not_performed"
    assert record["recurrence_prediction"] == "not_performed"
    assert record["crosses_resection"] is False
    assert record["interval"] == "week-045 to week-049"


def test_root_reads_local_config_only_when_repo_root_is_given(tmp_path, monkeypatch):
    monkeypatch.delenv("LUMIERE_P048_ROOT", raising=False)
    prepared = tmp_path / "prepared"
    marker = prepared / "derivatives/tp-week-000-1/seg_dl/tp-week-000-1_seg_brats3_dl.nii.gz"
    marker.parent.mkdir(parents=True)
    marker.touch()
    (tmp_path / "local").mkdir()
    (tmp_path / "local/lumiere-case.json").write_text(json.dumps({"prepared_root": str(prepared)}))
    assert lumiere_p048_root() is None
    assert lumiere_p048_root(tmp_path) == prepared
    monkeypatch.setenv("LUMIERE_P048_ROOT", str(tmp_path / "missing"))
    assert lumiere_p048_root(tmp_path) is None


@pytest.mark.skipif(
    lumiere_p048_root(REPO_ROOT) is None, reason="LUMIERE Patient-048 extract is absent"
)
def test_patient048_slice_cuts_tumor_and_stays_prescribed():
    result = illustrate_patient048(lumiere_p048_root(REPO_ROOT))
    areas = {visit["name"]: visit["whole_tumor_area_mm2"] for visit in result["visits"]}
    assert all(area > 0 for area in areas.values())
    assert result["solved_interval_days"] == 28
    assert result["parameters"]["n_steps"] == 112
    assert 0.0 <= result["comparison_dice"] <= 1.0
    assert 0.0 <= result["baseline_dice"] <= 1.0
    assert 0.0 <= result["alternative"]["comparison_dice"] <= 1.0
    assert result["alternative"]["diffusivity_mm2_per_day"] == 1.0
    assert (
        result["alternative"]["proliferation_per_day"]
        == result["parameters"]["proliferation_per_day"]
    )
    missed = result["largest_uncovered_component"]
    assert result["largest_uncovered_component_mm2"] > 0
    assert missed["area_mm2"] == (
        missed["edema"] + missed["enhancing_tumor"] + missed["necrosis_or_non_enhancing"]
    )
    assert missed["expert_recontour"] == "not_performed"
    assert missed["registration_reestimated"] == "not_performed"
    initial = result["compartments_mm2"]["week-045"]
    initial_visit = next(visit for visit in result["visits"] if visit["name"] == "week-045")
    assert sum(initial.values()) == initial_visit["whole_tumor_area_mm2"]
    assert result["density_min"] >= -1e-8
    assert result["specification"] == slice_specification()
    drawn = [visit["name"] for visit in result["visits"] if visit["drawn"]]
    assert drawn == ["week-000-1", "week-000-2", "week-045", "week-049"]
