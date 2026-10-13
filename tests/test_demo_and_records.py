"""Checks for construction, provenance, missing evidence, and finite eligibility."""

import copy
import json

import numpy as np
import pytest

from glioma_ai.assistance import validate_record
from glioma_ai.cgga_clinical import _usable_survival
from glioma_ai.demo import run_demo
from glioma_ai.imaging import summarize_labels
from glioma_ai.provenance import sha256


def test_demo_links_physical_measurements_to_generated_evidence(tmp_path):
    results = run_demo(tmp_path, tmp_path / "paper")
    image = results["imaging"]
    measured = summarize_labels(tmp_path / "synthetic_labels.nii.gz", [1, 2, 4])
    assert measured["selected_volume_ml"] == pytest.approx(image["reference_volume_ml"])
    assert sum(image["volume_by_label_ml"].values()) == pytest.approx(image["reference_volume_ml"])
    assert image["translated_dice"] < 1
    assert image["expanded_relative_volume_error"] > 0
    arrays = np.load(tmp_path / "synthetic_density.npz")
    assert arrays["density"].sum() > arrays["initial"].sum()
    dynamics = results["dynamics"]
    assert dynamics["area_at_threshold_005_mm2"] > dynamics["area_at_threshold_05_mm2"]
    assert dynamics["density_min"] >= -1e-12
    assert dynamics["density_max"] <= 1 + 1e-12
    niche = results["microenvironment"]
    assert niche["total_density_change_max_abs"] < 1e-15
    assert niche["final_mes_like_fraction"] > niche["no_cue_final_mes_like_fraction"]
    neural = results["neuron_glioma"]
    integrals = neural["final_density_integral_mm2"]
    assert integrals["feedback"] > integrals["one_way"] > integrals["baseline"]
    assert neural["step_halving_relative_integral_difference"] < 0.01
    np.testing.assert_allclose(
        np.array(neural["sensitivity"]["integral_ratio_to_baseline"])[:, 0], 1
    )
    assert neural["calibration"] == "not_performed"
    assert set(results["assistant_endpoints"].values()) == {"not_measured"}
    record = json.loads((tmp_path / "run.json").read_text())
    for name, digest in record["output_sha256"].items():
        assert sha256(tmp_path / name) == digest
    assert "src/glioma_ai/demo.py" in record["source_sha256"]
    macros = (tmp_path / "paper/numbers.tex").read_text()
    assert f"{{{image['reference_volume_ml']:.3f}}}" in macros
    related = record["related_published_evidence"]
    assert related["evidence_type"] == "published_reported"
    assert related["inference_rerun"] is False
    assert sha256(tmp_path / related["file"]) == related["sha256"]
    assert all(
        results[name]["evidence_type"] == "synthetic"
        for name in (
            "imaging",
            "dynamics",
            "microenvironment",
            "neuron_glioma",
        )
    )


@pytest.mark.parametrize("value", ["inf", "-inf", "NaN", "-1", "not-a-number"])
def test_survival_eligibility_rejects_nonfinite_or_invalid_time(value):
    assert not _usable_survival({"OS": value, "Censor (alive=0; dead=1)": "1"})


def completed_record():
    return {
        "schema": "glioma-ai-assistance-v1",
        "date": "2026-10-06",
        "task": "Document a synthetic measurement implementation",
        "tool": "Codex desktop",
        "model": "unknown",
        "input_classification": "synthetic only",
        "instruction_summary": "Generate physical volumes with explicit units",
        "contribution": "Code and documentation",
        "artifact_reference": "src/glioma_ai/demo.py",
        "checks": ["Independent voxel determinant test"],
        "decision": "pending_human_review",
        "reviewer": None,
        "unresolved_questions": ["Clinical relevance"],
        "record_type": "retrospective_summary",
    }


def test_record_cannot_invent_review_or_omit_evidence():
    record = completed_record()
    assert validate_record(record) == record
    invalid = copy.deepcopy(record)
    invalid["decision"] = "accepted"
    with pytest.raises(ValueError, match="reviewer"):
        validate_record(invalid)
    invalid = copy.deepcopy(record)
    invalid["checks"] = []
    with pytest.raises(ValueError, match="check"):
        validate_record(invalid)
    invalid = copy.deepcopy(record)
    invalid["task"] = "REPLACE"
    with pytest.raises(ValueError, match="task"):
        validate_record(invalid)
