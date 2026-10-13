"""Released LUMIERE metadata is read per patient, hashed and kept at week resolution."""

import json

import pytest

from glioma_ai.lumiere_metadata import (
    SOURCE_FILES,
    case_reference,
    nominal_day,
    read_case_metadata,
    scanner_summary,
)
from glioma_ai.lumiere_slice import VISITS

RATING = '"Rating (according to RANO, PD: Progressive disease)"'
RATIONALE = '"Rating rationale (CRET: complete resection)"'


def write_tables(directory):
    tables = {
        "demographics_pathology": (
            "Patient,Survival time (weeks),Sex,Age at surgery (years)\n"
            "Patient-001,40,male,61\nPatient-002,90,female,48\n"
        ),
        "expert_rating": (
            f"Patient,Date,LessThan3Months,NonMeasurableLesions,{RATING},{RATIONALE}\n"
            "Patient-001,week-000-1,,,Pre-Op,\n"
            "Patient-001,week-012,,x,PD,new L.\n"
            "Patient-002,week-000-1,,,Pre-Op,\n"
        ),
        "mr_info": (
            "Patient,Timepoint,Sequence,Field strength,Manufacturer,Model,Acquisition type,"
            "Slice thickness,Voxel size,Sex,Age\n"
            "Patient-001,week-000-1,CT1,1.5,SIEMENS ,Aera,3D,1,1\\1 ,M ,061Y\n"
            "Patient-001,week-012,CT1,3,SIEMENS ,Skyra,3D,1,1\\1 ,M ,061Y\n"
        ),
        "data_completeness": (
            "Patient,Timepoint,CT1,T1\nPatient-001,week-000-1,x,x\nPatient-001,week-012,x,\n"
        ),
    }
    for key, text in tables.items():
        (directory / SOURCE_FILES[key]).write_text(text, encoding="utf-8")


def test_reads_only_the_requested_patient_and_hashes_sources(tmp_path):
    write_tables(tmp_path)
    case = read_case_metadata(tmp_path, "Patient-001")
    assert case["patient_level"] == {
        "Survival time (weeks)": "40",
        "Sex": "male",
        "Age at surgery (years)": "61",
    }
    assert [v["visit"] for v in case["visits"]] == ["week-000-1", "week-012"]
    later = case["visits"][1]
    assert later["rano_rating"] == "PD" and later["non_measurable_lesions"]
    assert later["available"] == ["CT1"]
    assert later["nominal_day"] == 84
    assert "Sex" not in later["mri"][0] and later["mri"][0]["Manufacturer"] == "SIEMENS"
    assert scanner_summary(later) == "3 T SIEMENS Skyra"
    assert set(case["source"]["files"]) == set(SOURCE_FILES.values())
    assert all(len(digest) == 64 for digest in case["source"]["files"].values())


def test_missing_tables_or_patient_are_refused(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_case_metadata(tmp_path, "Patient-001")
    write_tables(tmp_path)
    with pytest.raises(ValueError):
        read_case_metadata(tmp_path, "Patient-999")


def test_nominal_day_uses_the_released_week_bin():
    assert nominal_day("week-045") == 315
    assert nominal_day("week-000-2") == 0


def test_tracked_patient_048_reference_matches_the_prepared_visits():
    case = case_reference()
    assert case["patient"] == "Patient-048"
    assert [(v["visit"], v["rano_rating"]) for v in case["visits"]] == [
        (visit["name"], visit["rating"]) for visit in VISITS
    ]
    assert "non-commercial" in case["source"]["use_condition"]
    assert "/Users/" not in json.dumps(case)
