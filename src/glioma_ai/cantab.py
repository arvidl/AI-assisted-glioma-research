"""Read a pinned behavioral release without pooling diagnoses or inventing scores."""

import csv
import json
import math
import urllib.request
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path

from glioma_ai.provenance import sha256

REFERENCE = Path(__file__).parent / "references/cantab_osf.json"
MISSING = {"", "NA", "N/A"}
METRICS = {
    "MOT_latency_mean": {
        "local": "mot_latency_mean",
        "name": "Motor screening",
        "unit": "ms",
        "sense": -1,
    },
    "RTI_fiveRT": {
        "local": "rti_five_rt",
        "name": "Processing speed",
        "unit": "ms",
        "sense": -1,
    },
    "RVP_A": {
        "local": "rvp_a",
        "name": "Sustained attention",
        "unit": "A prime",
        "sense": 1,
    },
    "SOC_prob_minmoves": {
        "local": "soc_prob_min_moves",
        "name": "Spatial planning",
        "unit": "problems",
        "sense": 1,
    },
    "SSP_spanlength": {
        "local": "ssp_span_length",
        "name": "Spatial working memory",
        "unit": "span",
        "sense": 1,
    },
}
DOMAINS = tuple(key for key in METRICS if not key.startswith("MOT"))


def release_reference() -> dict:
    return json.loads(REFERENCE.read_text())


def fetch_release(directory: Path) -> dict:
    """Explicit network acquisition; pin revision and bytes, and never print rows."""
    import hashlib

    directory = Path(directory)
    pending = {}
    for name, spec in release_reference()["files"].items():
        path = directory / name
        if path.is_file():
            if sha256(path) != spec["sha256"]:
                raise ValueError(f"Existing {name} differs from the pinned release; preserve it.")
            continue
        with urllib.request.urlopen(spec["download_url"], timeout=45) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != spec["sha256"]:
            raise ValueError(f"Downloaded {name} differs from the pinned release.")
        pending[name] = content
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in pending.items():
        (directory / name).write_bytes(content)
    return {"source": release_reference()["project_url"], "files": verify_release(directory)}


def verify_release(directory: Path) -> dict:
    hashes = {}
    for name, spec in release_reference()["files"].items():
        path = Path(directory) / name
        if not path.is_file() or sha256(path) != spec["sha256"]:
            raise ValueError(f"Missing or changed pinned source: {name}.")
        hashes[name] = spec["sha256"]
    return hashes


def numeric(value: str) -> float | None:
    value = value.strip()
    if value.upper() in MISSING:
        return None
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError("Invalid numeric score.") from error
    if not math.isfinite(number):
        raise ValueError("Nonfinite score is not a missing-data marker.")
    return number


def assessment_interval(row: dict) -> int | None:
    if row["date_t2"].strip().upper() in MISSING:
        return None
    first, second = (datetime.strptime(row[f"date_t{t}"], "%d/%m/%y") for t in (1, 2))
    days = (second - first).days
    if days <= 0:
        raise ValueError("Follow-up must be after the baseline assessment.")
    return days


def read_release(directory: Path) -> list[dict]:
    verify_release(directory)
    return read_behavioral_csv(Path(directory) / "Data.csv")


def read_behavioral_csv(path: Path) -> list[dict]:
    """Strict schema for this source; no imputation, normalization or ID guessing."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"subID", "group", "date_t1", "date_t2"}
        required.update(f"{key}_t{t}" for key in METRICS for t in (1, 2))
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Behavioral table lacks required source columns.")
        rows = list(reader)
    identifiers = set()
    for row in rows:
        identifier = row["subID"].strip()
        if not identifier or identifier in identifiers:
            raise ValueError("Source IDs must be populated and unique.")
        identifiers.add(identifier)
        if row["group"] not in {"GLI", "MEN", "CON"}:
            raise ValueError("Unknown diagnosis group; do not silently relabel it.")
        datetime.strptime(row["date_t1"], "%d/%m/%y")
        days = assessment_interval(row)
        for key in METRICS:
            for t in (1, 2):
                score = numeric(row[f"{key}_t{t}"])
                if score is None:
                    continue
                if t == 2 and days is None:
                    raise ValueError("A follow-up score needs its assessment date.")
                if key == "RVP_A" and not 0 <= score <= 1:
                    raise ValueError("RVP sensitivity must be within 0 to 1.")
                if key in {"SOC_prob_minmoves", "SSP_spanlength"}:
                    if score < 0 or not score.is_integer():
                        raise ValueError("Planning and span scores must be nonnegative counts.")
                if METRICS[key]["unit"] == "ms" and score <= 0:
                    raise ValueError("A latency must be positive in milliseconds.")
    return rows


def cohort_summary(rows: list[dict]) -> dict:
    """Export availability counts only, keeping diagnosis groups separate."""
    groups = {}
    for group in ("GLI", "MEN", "CON"):
        subset = [row for row in rows if row["group"] == group]
        pairs = {
            key: sum(all(numeric(row[f"{key}_t{t}"]) is not None for t in (1, 2)) for row in subset)
            for key in METRICS
        }
        complete = sum(
            all(numeric(row[f"{key}_t{t}"]) is not None for key in DOMAINS for t in (1, 2))
            for row in subset
        )
        groups[group] = {
            "baseline_rows": len(subset),
            "paired_by_measure": pairs,
            "complete_four_domains": complete,
        }
    return {
        "evidence_type": "released_behavioral_observations",
        "n_rows": len(rows),
        "groups": groups,
        "mri_linkage_and_qc": "not_performed",
    }


def precision_agreement(source: str, local: str) -> str:
    """Check extra digits only at the published score's decimal resolution."""
    if numeric(source) is None or numeric(local) is None:
        return "missing"
    try:
        a, b = Decimal(source), Decimal(local)
        if a == b:
            return "exact"
        quantum = Decimal(1).scaleb(a.as_tuple().exponent)
        if b.quantize(quantum, rounding=ROUND_HALF_EVEN) == a:
            return "at_release_precision"
    except InvalidOperation as error:
        raise ValueError("Invalid decimal score.") from error
    return "mismatch"


def precision_interval(source: str) -> dict:
    """Values that round (half-even) to a released score at its own decimal resolution.

    Returns the quantum (last released digit) and the half-quantum bounds. Whether a
    value exactly on a bound rounds to the score depends on half-even rounding, as in
    precision_agreement.
    """
    if numeric(source) is None:
        raise ValueError("A released score is required.")
    value = Decimal(source)
    quantum = Decimal(1).scaleb(value.as_tuple().exponent)
    return {
        "quantum": float(quantum),
        "low": float(value - quantum / 2),
        "high": float(value + quantum / 2),
    }


def reliable_change_index(
    baseline: float, follow_up: float, baseline_sd: float, reliability: float
) -> dict:
    """Jacobson-Truax reliable change index (doi:10.1037/0022-006X.59.1.12).

    SE = SD * sqrt(1 - r); S_diff = sqrt(2) * SE; RCI = (follow_up - baseline) / S_diff.
    |RCI| > 1.96 is conventionally called reliable at the two-sided 5% level. SD and r
    must come from a compatible reference sample; this classic form ignores practice
    effects and regression to the mean. Direction (better/worse) depends on the measure.
    """
    values = [baseline, follow_up, baseline_sd, reliability]
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError("Inputs must be finite.")
    if baseline_sd <= 0 or not 0 <= reliability < 1:
        raise ValueError("Require SD > 0 and reliability in [0, 1).")
    standard_error = baseline_sd * math.sqrt(1 - reliability)
    s_diff = math.sqrt(2) * standard_error
    index = (follow_up - baseline) / s_diff
    return {
        "standard_error": standard_error,
        "s_diff": s_diff,
        "rci": index,
        "minimum_reliable_change": 1.96 * s_diff,
        "reliable": abs(index) > 1.96,
    }


def verified_case(rows: list[dict], sessions_path: Path, source_case_id: str) -> dict:
    """Match an explicit local ID; exported result omits IDs, dates and demographics."""
    matches = [row for row in rows if row["subID"] == source_case_id]
    if len(matches) != 1 or matches[0]["group"] != "GLI":
        raise ValueError("Require one explicit glioma ID in the source release.")
    with Path(sessions_path).open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        local_rows = list(reader)
        fields = reader.fieldnames or []
    if len(local_rows) != 2 or {r["session_id"] for r in local_rows} != {"ses-preop", "ses-postop"}:
        raise ValueError("Require exactly one preoperative and one follow-up session.")
    local = {row["session_id"]: row for row in local_rows}
    source = matches[0]
    audit, scores = [], {}
    for key, spec in METRICS.items():
        values = []
        for t, visit in ((1, "ses-preop"), (2, "ses-postop")):
            a, b = source[f"{key}_t{t}"], local[visit][spec["local"]]
            status = precision_agreement(a, b)
            if status in {"mismatch", "missing"}:
                raise ValueError(f"Cannot verify {key} at visit {t}: {status}.")
            audit.append({"measure": key, "visit": t, "agreement": status})
            values.append(numeric(a))
        scores[key] = {
            "before": values[0],
            "followup": values[1],
            "released_text": [source[f"{key}_t1"], source[f"{key}_t2"]],
            "unit": spec["unit"],
            "raw_delta": values[1] - values[0],
        }
    local_metrics = [k for k in fields if k.startswith(("mot_", "rti_", "rvp_", "soc_", "ssp_"))]
    return {
        "evidence_type": "source_verified_single_case_observations",
        "assessment_interval_days": assessment_interval(source),
        "scores": scores,
        "audit": audit,
        "local_cantab_metric_count": len(local_metrics),
        "verified_metric_count": len(METRICS),
        "sessions_sha256": sha256(sessions_path),
        "interpretation": "descriptive at release precision; reliable change not assessed",
        "causal_resection_effect": "not_identified",
        "prediction": "not_performed",
    }
