"""Synthetic controls for provenance, pairing, precision and evidence boundaries."""

import csv
import json

import pytest

from glioma_ai.cantab import (
    DOMAINS,
    METRICS,
    assessment_interval,
    cohort_summary,
    numeric,
    precision_agreement,
    read_behavioral_csv,
    release_reference,
    verified_case,
    verify_release,
)


def constructed_row(identifier="constructed-A", group="GLI"):
    row = {"subID": identifier, "group": group, "date_t1": "01/01/25", "date_t2": "10/07/25"}
    for key in METRICS:
        value = "0.70" if key == "RVP_A" else "120.00" if METRICS[key]["unit"] == "ms" else "3"
        row.update({f"{key}_t1": value, f"{key}_t2": value})
    return row


def table(tmp_path, rows):
    path = tmp_path / "constructed.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_counts_keep_missingness_and_diagnoses_separate(tmp_path):
    rows = [
        constructed_row(),
        constructed_row("constructed-B"),
        constructed_row("constructed-C", "MEN"),
        constructed_row("constructed-D", "CON"),
    ]
    rows[1]["RVP_A_t2"] = "NA"
    actual = cohort_summary(read_behavioral_csv(table(tmp_path, rows)))
    assert actual["n_rows"] == 4
    assert actual["groups"]["GLI"]["complete_four_domains"] == 1
    assert actual["groups"]["GLI"]["paired_by_measure"]["RTI_fiveRT"] == 2
    assert actual["groups"]["GLI"]["paired_by_measure"]["RVP_A"] == 1
    assert actual["groups"]["MEN"]["complete_four_domains"] == 1
    assert "constructed-A" not in json.dumps(actual)
    assert actual["mri_linkage_and_qc"] == "not_performed"


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "unknown"])
def test_nonfinite_scores_do_not_become_missing(value):
    with pytest.raises(ValueError):
        numeric(value)


def test_release_precision_cannot_support_extra_digit_change():
    assert precision_agreement("0.70", "0.700") == "exact"
    assert precision_agreement("0.70", "0.702") == "at_release_precision"
    assert precision_agreement("0.70", "0.72") == "mismatch"
    assert precision_agreement("NA", "0.70") == "missing"


@pytest.mark.parametrize("defect", ["duplicate", "group", "date", "missing_date", "range", "count"])
def test_reader_refuses_ambiguous_or_invalid_observations(tmp_path, defect):
    rows = [constructed_row()]
    if defect == "duplicate":
        rows.append(constructed_row())
    elif defect == "group":
        rows[0]["group"] = "unknown"
    elif defect == "date":
        rows[0]["date_t2"] = "01/01/24"
    elif defect == "missing_date":
        rows[0]["date_t2"] = "NA"
    elif defect == "range":
        rows[0]["RVP_A_t2"] = "1.2"
    else:
        rows[0]["SSP_spanlength_t2"] = "2.5"
    with pytest.raises(ValueError):
        read_behavioral_csv(table(tmp_path, rows))


def test_case_uses_released_scores_and_does_not_export_identity(tmp_path):
    row = constructed_row()
    sessions = []
    for visit in ("ses-preop", "ses-postop"):
        local = {"session_id": visit}
        local.update({spec["local"]: row[f"{key}_t1"] for key, spec in METRICS.items()})
        if visit == "ses-postop":
            local["rvp_a"] = "0.702"
        sessions.append(local)
    path = tmp_path / "constructed_sessions.tsv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(sessions[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(sessions)
    case = verified_case([row], path, "constructed-A")
    assert case["scores"]["RVP_A"]["raw_delta"] == 0
    assert sum(a["agreement"] == "at_release_precision" for a in case["audit"]) == 1
    assert case["assessment_interval_days"] == assessment_interval(row)
    assert case["verified_metric_count"] == 5
    assert "constructed-A" not in json.dumps(case)
    assert "01/01/25" not in json.dumps(case)
    assert case["prediction"] == "not_performed"
    assert len(DOMAINS) == 4
    with pytest.raises(ValueError, match="explicit glioma"):
        verified_case([row], path, "constructed-absent")


def test_unverified_source_cannot_make_an_empirical_result(tmp_path):
    (tmp_path / "Data.csv").write_text("not the pinned release")
    with pytest.raises(ValueError, match="pinned source"):
        verify_release(tmp_path)
    reference = release_reference()
    assert reference["files"]["Data.csv"]["revision"] == 2
    assert reference["data_in_git"] is False
    assert all(len(s["sha256"]) == 64 for s in reference["files"].values())
