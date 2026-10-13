"""Released LUMIERE metadata for one patient, read from the dataset's CSV tables.

The LUMIERE release (Suter et al. 2022) provides anonymized per-patient
demographics and pathology, expert RANO ratings per visit, MRI acquisition
parameters and data completeness as CSV files. Dates are released as week
counts relative to the pre-operative scan; nothing finer is derived here.
"""

import csv
import hashlib
import json
from importlib import resources
from pathlib import Path

ARTICLE_DOI = "10.1038/s41597-022-01881-7"
FIGSHARE_DOI = "10.6084/m9.figshare.c.5904905.v1"
USE_CONDITION = (
    "Figshare files labelled CC0; the authors state that the dataset may only be used "
    "for non-commercial purposes (Suter et al. 2022, Usage Notes)."
)
SOURCE_FILES = {
    "demographics_pathology": "LUMIERE-Demographics_Pathology.csv",
    "expert_rating": "LUMIERE-ExpertRating-v202211.csv",
    "mr_info": "LUMIERE-MRinfo.csv",
    "data_completeness": "LUMIERE-datacompleteness.csv",
}
RATING_COLUMN_PREFIX = "Rating (according to RANO"
RATIONALE_COLUMN_PREFIX = "Rating rationale"
MR_FIELDS = (
    "Sequence",
    "Field strength",
    "Manufacturer",
    "Model",
    "Acquisition type",
    "Slice thickness",
    "Voxel size",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path, patient: str) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            {key.strip(): (value or "").strip() for key, value in row.items()}
            for row in reader
            if row["Patient"].strip() == patient
        ]
        return [name.strip() for name in reader.fieldnames or []], rows


def _column(fieldnames: list[str], prefix: str) -> str:
    matches = [name for name in fieldnames if name.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one column starting with {prefix!r}, found {matches}")
    return matches[0]


def nominal_day(visit: str) -> int:
    """Week label times seven; LUMIERE blurs intervals to weeks, so this is +/-3 days."""
    return 7 * int(visit.split("-")[1])


def read_case_metadata(lumiere_dir: Path, patient: str) -> dict:
    """Collect one patient's released rows, with the SHA-256 of each source table."""
    paths = {key: Path(lumiere_dir) / name for key, name in SOURCE_FILES.items()}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"LUMIERE tables not found: {missing}")

    _, demographics = _rows(paths["demographics_pathology"], patient)
    if len(demographics) != 1:
        raise ValueError(f"Expected one demographics row for {patient}, found {len(demographics)}")
    patient_row = {k: v for k, v in demographics[0].items() if k != "Patient"}

    rating_fields, ratings = _rows(paths["expert_rating"], patient)
    rating_column = _column(rating_fields, RATING_COLUMN_PREFIX)
    rationale_column = _column(rating_fields, RATIONALE_COLUMN_PREFIX)
    _, mr_rows = _rows(paths["mr_info"], patient)
    completeness_fields, completeness = _rows(paths["data_completeness"], patient)
    available = [name for name in completeness_fields if name not in {"Patient", "Timepoint"}]

    visits = []
    for row in ratings:
        visit = row["Date"]
        visits.append(
            {
                "visit": visit,
                "nominal_day": nominal_day(visit),
                "rano_rating": row[rating_column],
                "rating_rationale": row[rationale_column],
                "less_than_3_months": row.get("LessThan3Months") == "x",
                "non_measurable_lesions": row.get("NonMeasurableLesions") == "x",
                "mri": [
                    {field: mr[field] for field in MR_FIELDS}
                    for mr in mr_rows
                    if mr["Timepoint"] == visit
                ],
                "available": [
                    name
                    for row_c in completeness
                    if row_c["Timepoint"] == visit
                    for name in available
                    if row_c[name] == "x"
                ],
            }
        )
    if not visits:
        raise ValueError(f"No expert-rated visits for {patient}")
    return {
        "patient": patient,
        "source": {
            "article_doi": ARTICLE_DOI,
            "figshare_doi": FIGSHARE_DOI,
            "use_condition": USE_CONDITION,
            "files": {name: _sha256(paths[key]) for key, name in SOURCE_FILES.items()},
            "dates": "week counts relative to the pre-operative scan, as released",
        },
        "patient_level": patient_row,
        "visits": visits,
    }


def case_reference(name: str = "lumiere_p048") -> dict:
    """Tracked metadata extracted by scripts/extract_lumiere_metadata.py."""
    source = resources.files("glioma_ai").joinpath(f"references/{name}.json")
    return json.loads(source.read_text(encoding="utf-8"))


def scanner_summary(visit: dict) -> str:
    """Field strength, manufacturer and model(s) used at one visit."""
    combos = sorted(
        {f"{m['Field strength']} T {m['Manufacturer']} {m['Model']}" for m in visit["mri"]}
    )
    return "; ".join(combos)
