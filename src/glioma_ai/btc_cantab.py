"""CANTAB and metadata of the Brain Tumor Connectomics cohort (OpenNeuro ds001226/ds002080).

The two participants.tsv tables (CC0) are pinned by version, commit and SHA-256 in
references/btc_cantab.json, together with the digital-twin project's session table
for sub-PAT16. Acquisition is an explicit step (make btc-fetch); reading never
downloads. Tumour labels are mapped to the source authors' groups (GLI, MEN, CON)
by an explicit table, and an unknown label is an error. Exports are group-level,
except for the one case that is named explicitly. Change indices computed from the
ten retested controls are exploratory: a small caregiver sample is not a norm.
"""

import csv
import hashlib
import json
import math
import urllib.request
from pathlib import Path

import numpy as np

from glioma_ai.cantab import precision_agreement
from glioma_ai.provenance import sha256

REFERENCE = Path(__file__).parent / "references/btc_cantab.json"
MISSING = {"", "n/a", "NA"}
SESSIONS = ("preop", "postop")
TABLES = {"preop": "ds001226_participants.tsv", "postop": "ds002080_participants.tsv"}
CASE = "sub-PAT16"
# The OSF behavioural release uses the same authors' IDs without the BIDS prefix.
# The crosswalk is an assumption that cross_source_agreement checks score by score.
OSF_ID = {CASE: "PAT16"}
# Five-choice reaction-time columns whose names and summary statistics are audited.
RTI_AUDIT_COLUMNS = ("RTI_fiveRT", "RTI_fiveMT", "RTI_fiveMT_mean", "RTI_fiveMT_md")

# Every tumour label in the two tables, mapped to the group of the OSF behavioural
# release by the same authors (where the single ependymoma is in GLI).
GROUP_OF_LABEL = {
    "none": "CON",
    "Meningioma I": "MEN",
    "Meningioma II": "MEN",
    "Glioma II": "GLI",
    "Astrocytoma II": "GLI",
    "Oligodendroglioma II": "GLI",
    "Oligo-astrocytoma II": "GLI",
    "Oligo-astrocytoma III": "GLI",
    "Anaplastic astrocytoma III": "GLI",
    "Anaplastic astrocytoma II-III": "GLI",
    "Ependymoma II": "GLI",
}
GROUPS = {
    "CON": "Controls (partners or caregivers)",
    "MEN": "Meningioma",
    "GLI": "Glioma (source group, includes one ependymoma)",
}

MEASURES = {
    "MOT_latency_mean": {
        "short": "Motor latency",
        "test": "MOT",
        "name": "Motor screening latency",
        "construct": "sensorimotor speed and task comprehension (a screen, not a cognitive domain)",
        "unit": "ms",
        "sense": -1,
        "bounds": (0.0, None),
        "integer": False,
        "twin": "mot_latency_mean",
        "osf": "MOT_latency_mean",
    },
    "RTI_simpleRT_mean": {
        "short": "Simple reaction time",
        "test": "RTI",
        "name": "Simple reaction time",
        "construct": "alertness and simple processing speed",
        "unit": "ms",
        "sense": -1,
        "bounds": (0.0, None),
        "integer": False,
        "twin": "rti_simple_rt_mean",
        "osf": None,
    },
    "RTI_fiveRT": {
        "short": "Five-choice reaction time",
        "test": "RTI",
        "name": "Five-choice reaction time",
        "construct": "choice processing speed",
        "unit": "ms",
        "sense": -1,
        "bounds": (0.0, None),
        "integer": False,
        "twin": "rti_five_rt",
        "osf": "RTI_fiveRT",
    },
    "RVP_A": {
        "short": "RVP A′",
        "test": "RVP",
        "name": "Rapid visual processing A′",
        "construct": "sustained attention (target sensitivity)",
        "unit": "A′ (0 to 1)",
        "sense": 1,
        "bounds": (0.0, 1.0),
        "integer": False,
        "twin": "rvp_a",
        "osf": "RVP_A",
    },
    "SOC_prob_minmoves": {
        "short": "SOC minimum-move problems",
        "test": "SOC",
        "name": "Stockings of Cambridge, problems solved in minimum moves",
        "construct": "spatial planning",
        "unit": "problems (0 to 12)",
        "sense": 1,
        "bounds": (0.0, 12.0),
        "integer": True,
        "twin": "soc_prob_min_moves",
        "osf": "SOC_prob_minmoves",
    },
    "SSP_spanlength": {
        "short": "Spatial span",
        "test": "SSP",
        "name": "Spatial span length",
        "construct": "visuospatial short-term memory",
        "unit": "span (2 to 9)",
        "sense": 1,
        "bounds": (0.0, 9.0),
        "integer": True,
        "twin": "ssp_span_length",
        "osf": "SSP_spanlength",
    },
}


def btc_reference() -> dict:
    return json.loads(REFERENCE.read_text())


def verify_btc(directory: Path) -> dict:
    hashes = {}
    for name, spec in btc_reference()["files"].items():
        path = Path(directory) / name
        if not path.is_file() or sha256(path) != spec["sha256"]:
            raise ValueError(f"Missing or changed pinned source: {name}.")
        hashes[name] = spec["sha256"]
    return hashes


def fetch_btc(directory: Path) -> dict:
    """Explicit network acquisition of the pinned tables; nothing is written unverified."""
    directory = Path(directory)
    pending = {}
    for name, spec in btc_reference()["files"].items():
        path = directory / name
        if path.is_file():
            if sha256(path) != spec["sha256"]:
                raise ValueError(f"Existing {name} differs from the pinned source; preserve it.")
            continue
        with urllib.request.urlopen(spec["download_url"], timeout=60) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != spec["sha256"]:
            raise ValueError(f"Downloaded {name} differs from the pinned source.")
        pending[name] = content
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in pending.items():
        (directory / name).write_bytes(content)
    return {"license": btc_reference()["license"], "files": verify_btc(directory)}


def _number(text: str) -> float | None:
    text = text.strip()
    if text in MISSING:
        return None
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("Nonfinite score is not a missing-data marker.")
    return value


def read_table(path: Path) -> dict[str, dict[str, str]]:
    """Rows by participant ID, with the stray spaces of the source headers removed."""
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        rows = [{key.strip(): value.strip() for key, value in row.items()} for row in reader]
    table = {}
    for row in rows:
        identifier = row.get("participant_id", "")
        if not identifier or identifier in table:
            raise ValueError("Participant IDs must be populated and unique.")
        table[identifier] = row
    return table


def _scores(row: dict[str, str]) -> dict[str, float | None]:
    scores = {}
    for code, spec in MEASURES.items():
        value = _number(row[code])
        if value is not None:
            low, high = spec["bounds"]
            if value < low or (high is not None and value > high):
                raise ValueError(f"{code} = {value} lies outside its scale.")
            if spec["integer"] and not value.is_integer():
                raise ValueError(f"{code} must be a whole count.")
        scores[code] = value
    return scores


def load_cohort(directory: Path) -> list[dict]:
    """One record per participant: group, tumour label, scores per session, raw rows."""
    directory = Path(directory)
    verify_btc(directory)
    tables = {session: read_table(directory / TABLES[session]) for session in SESSIONS}
    if not set(tables["postop"]) <= set(tables["preop"]):
        raise ValueError("A follow-up participant lacks a baseline row.")
    cohort = []
    for identifier, row in tables["preop"].items():
        label = row["tumor type & grade"]
        if label not in GROUP_OF_LABEL:
            raise ValueError(f"Unknown tumour label {label!r}; extend GROUP_OF_LABEL explicitly.")
        follow = tables["postop"].get(identifier)
        if follow is not None and follow["tumor type & grade"] != label:
            raise ValueError(f"Tumour label differs between sessions for {identifier}.")
        cohort.append(
            {
                "id": identifier,
                "group": GROUP_OF_LABEL[label],
                "label": label,
                "location": row["tumor location"],
                "size_cm3": _number(row["tumor size (cub cm)"]),
                "scores": {
                    "preop": _scores(row),
                    "postop": None if follow is None else _scores(follow),
                },
                "raw": {"preop": row, "postop": follow},
            }
        )
    return cohort


def cohort_counts(cohort: list[dict]) -> dict:
    """Participants per group and session, and complete pairs per measure."""
    counts = {}
    for group in GROUPS:
        members = [p for p in cohort if p["group"] == group]
        tested = [p for p in members if any(v is not None for v in p["scores"]["preop"].values())]
        counts[group] = {
            "baseline_rows": len(members),
            "baseline_with_cantab": len(tested),
            "followup_rows": sum(p["scores"]["postop"] is not None for p in members),
            "pairs": {code: len(paired_values(cohort, code, group)[0]) for code in MEASURES},
        }
    return counts


def group_values(cohort: list[dict], code: str, session: str, group: str) -> np.ndarray:
    values = [
        p["scores"][session][code]
        for p in cohort
        if p["group"] == group
        and p["scores"][session] is not None
        and p["scores"][session][code] is not None
    ]
    return np.array(values, dtype=float)


def paired_values(
    cohort: list[dict], code: str, group: str, exclude: tuple[str, ...] = ()
) -> tuple[np.ndarray, np.ndarray]:
    pairs = [
        (p["scores"]["preop"][code], p["scores"]["postop"][code])
        for p in cohort
        if p["group"] == group
        and p["id"] not in exclude
        and p["scores"]["postop"] is not None
        and p["scores"]["preop"][code] is not None
        and p["scores"]["postop"][code] is not None
    ]
    array = np.array(pairs, dtype=float).reshape(-1, 2)
    return array[:, 0], array[:, 1]


def group_summary(cohort: list[dict], code: str) -> list[dict]:
    """Median and quartiles per group and session; no individual values."""
    rows = []
    for group in GROUPS:
        for session in SESSIONS:
            values = group_values(cohort, code, session, group)
            if values.size == 0:
                continue
            q1, median, q3 = np.percentile(values, [25, 50, 75])
            rows.append(
                {
                    "group": group,
                    "session": session,
                    "n": int(values.size),
                    "median": float(median),
                    "q1": float(q1),
                    "q3": float(q3),
                }
            )
    return rows


def case_scores(cohort: list[dict], case: str = CASE) -> dict:
    matches = [p for p in cohort if p["id"] == case]
    if len(matches) != 1 or matches[0]["scores"]["postop"] is None:
        raise ValueError(f"Require exactly one {case} with both sessions.")
    person = matches[0]
    return {
        "id": case,
        "group": person["group"],
        "label": person["label"],
        "location": person["location"],
        "size_cm3": person["size_cm3"],
        "scores": {
            code: (person["scores"]["preop"][code], person["scores"]["postop"][code])
            for code in MEASURES
        },
        "text": {
            code: (person["raw"]["preop"][code], person["raw"]["postop"][code]) for code in MEASURES
        },
    }


def retest_statistics(baseline: np.ndarray, follow_up: np.ndarray) -> dict | None:
    """Retest summary of a reference sample; None when a statistic is undefined."""
    x, y = np.asarray(baseline, float), np.asarray(follow_up, float)
    if x.size < 3 or x.size != y.size:
        raise ValueError("Require at least three paired reference scores.")
    sd_x, sd_y = x.std(ddof=1), y.std(ddof=1)
    if sd_x == 0 or sd_y == 0:
        return None
    r = float(np.corrcoef(x, y)[0, 1])
    if r >= 1:
        return None
    slope = float(np.cov(x, y, ddof=1)[0, 1] / sd_x**2)
    intercept = float(y.mean() - slope * x.mean())
    residual = y - (intercept + slope * x)
    see = float(np.sqrt((residual**2).sum() / (x.size - 2)))
    differences = y - x
    return {
        "n": int(x.size),
        "mean_baseline": float(x.mean()),
        "sd_baseline": float(sd_x),
        "mean_follow_up": float(y.mean()),
        "r": r,
        "practice": float(differences.mean()),
        "sd_difference": float(differences.std(ddof=1)),
        "slope": slope,
        "intercept": intercept,
        "see": see,
    }


def change_indices(baseline: float, follow_up: float, stats: dict) -> dict:
    """Three reliable-change indices, signed as follow-up minus expected.

    Jacobson-Truax: (x2 - x1) / S_diff with S_diff = sqrt(2) SD sqrt(1 - r).
    Practice-adjusted (Chelune et al. 1993): ((x2 - x1) - practice) / S_diff.
    Regression-based (McSweeny et al. 1993): (x2 - (a + b x1)) / SEE.
    """
    s_diff = math.sqrt(2) * stats["sd_baseline"] * math.sqrt(1 - stats["r"])
    change = follow_up - baseline
    predicted = stats["intercept"] + stats["slope"] * baseline
    if stats["see"] == 0:
        raise ValueError("The regression standard error is zero.")
    return {
        "jacobson_truax": change / s_diff,
        "practice_adjusted": (change - stats["practice"]) / s_diff,
        "regression_based": (follow_up - predicted) / stats["see"],
        "s_diff": s_diff,
        "predicted_follow_up": predicted,
    }


INDICES = {
    "jacobson_truax": "Jacobson–Truax",
    "practice_adjusted": "Practice-adjusted",
    "regression_based": "Regression-based",
}


def reading(index: float, sense: int, threshold: float = 1.96) -> str:
    if abs(index) <= threshold:
        return "within the reference variation"
    return "reliable improvement" if index * sense > 0 else "reliable decline"


def bootstrap_indices(
    reference_baseline: np.ndarray,
    reference_follow_up: np.ndarray,
    baseline: float,
    follow_up: float,
    n_boot: int = 4000,
    seed: int = 20261014,
) -> dict:
    """Percentile intervals of each index when the reference sample is resampled."""
    x, y = np.asarray(reference_baseline, float), np.asarray(reference_follow_up, float)
    rng = np.random.default_rng(seed)
    draws = {name: [] for name in INDICES}
    undefined = 0
    for _ in range(n_boot):
        pick = rng.integers(0, x.size, x.size)
        stats = retest_statistics(x[pick], y[pick])
        if stats is None or stats["see"] == 0:
            undefined += 1
            continue
        for name, value in change_indices(baseline, follow_up, stats).items():
            if name in draws:
                draws[name].append(value)
    return {
        "n_boot": n_boot,
        "undefined_resamples": undefined,
        "intervals": {
            name: tuple(float(v) for v in np.percentile(values, [2.5, 97.5]))
            for name, values in draws.items()
        },
        "share_beyond_threshold": {
            name: float(np.mean(np.abs(values) > 1.96)) for name, values in draws.items()
        },
    }


def case_change_table(
    cohort: list[dict], case: str = CASE, exclude: tuple[str, ...] = (), n_boot: int = 4000
) -> list[dict]:
    """Per measure: control retest statistics, the case's indices and bootstrap intervals."""
    person = case_scores(cohort, case)
    rows = []
    for code, spec in MEASURES.items():
        x, y = paired_values(cohort, code, "CON", exclude=exclude)
        stats = retest_statistics(x, y)
        before, after = person["scores"][code]
        if stats is None or before is None or after is None:
            rows.append({"measure": code, "defined": False})
            continue
        indices = change_indices(before, after, stats)
        boot = bootstrap_indices(x, y, before, after, n_boot=n_boot)
        rows.append(
            {
                "measure": code,
                "defined": True,
                "sense": spec["sense"],
                "unit": spec["unit"],
                "baseline": before,
                "follow_up": after,
                "reference": stats,
                **{name: indices[name] for name in INDICES},
                "readings": {name: reading(indices[name], spec["sense"]) for name in INDICES},
                "bootstrap": boot,
            }
        )
    return rows


def leave_one_out(baseline: np.ndarray, follow_up: np.ndarray) -> dict:
    """Mean absolute error of three follow-up forecasts, each person held out in turn.

    Persistence predicts the baseline; mean change adds the training mean change;
    regression fits follow-up on baseline in the training people.
    """
    x, y = np.asarray(baseline, float), np.asarray(follow_up, float)
    if x.size < 4:
        raise ValueError("Require at least four people.")
    errors = {"persistence": [], "mean_change": [], "regression": []}
    for i in range(x.size):
        keep = np.arange(x.size) != i
        errors["persistence"].append(abs(y[i] - x[i]))
        errors["mean_change"].append(abs(y[i] - (x[i] + (y[keep] - x[keep]).mean())))
        if np.ptp(x[keep]) == 0:
            prediction = y[keep].mean()
        else:
            slope, intercept = np.polyfit(x[keep], y[keep], 1)
            prediction = intercept + slope * x[i]
        errors["regression"].append(abs(y[i] - prediction))
    return {"n": int(x.size), **{name: float(np.mean(e)) for name, e in errors.items()}}


def forecast_table(cohort: list[dict], groups: tuple[str, ...] = tuple(GROUPS)) -> list[dict]:
    """Leave-one-out forecast errors per measure, pooling the listed groups."""
    rows = []
    for code in MEASURES:
        pairs = [paired_values(cohort, code, group) for group in groups]
        x = np.concatenate([p[0] for p in pairs])
        y = np.concatenate([p[1] for p in pairs])
        rows.append({"measure": code, "unit": MEASURES[code]["unit"], **leave_one_out(x, y)})
    return rows


def on_grid(values: np.ndarray, step: float = 0.5) -> float:
    """Share of values that are whole multiples of step."""
    scaled = np.asarray(values, float) / step
    return float(np.mean(np.isclose(scaled, np.round(scaled))))


def column_audit(
    cohort: list[dict], columns: tuple[str, ...] = RTI_AUDIT_COLUMNS, session: str = "preop"
) -> dict:
    """Group-level statistics that test what a column name claims.

    A median of an even number of whole-millisecond trials lies on a 0.5 ms grid;
    a mean usually does not. Correlations show which columns measure the same thing.
    """
    rows = []
    for person in cohort:
        raw = person["raw"][session]
        if raw is None:
            continue
        values = [_number(raw[column]) for column in columns]
        if None not in values:
            rows.append(values)
    data = np.array(rows, dtype=float)
    if len(data) < 3:
        raise ValueError("Require at least three complete rows.")
    correlation = np.corrcoef(data.T)
    return {
        "n": len(data),
        "columns": {
            column: {"median": float(np.median(data[:, i])), "half_ms_grid": on_grid(data[:, i])}
            for i, column in enumerate(columns)
        },
        "correlation": {
            a: {b: float(correlation[i, j]) for j, b in enumerate(columns)}
            for i, a in enumerate(columns)
        },
    }


def markdown_table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def read_twin_sessions(path: Path) -> dict[str, dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    sessions = {row["session_id"]: row for row in rows}
    if set(sessions) != {"ses-preop", "ses-postop"} or len(rows) != 2:
        raise ValueError("Require exactly one preoperative and one follow-up session.")
    return sessions


def cross_source_agreement(
    case: dict, twin_sessions: dict[str, dict[str, str]], osf_row: dict[str, str] | None
) -> list[dict]:
    """OpenNeuro is the record; the twin table and OSF are checked at their precision."""
    rows = []
    for code, spec in MEASURES.items():
        for visit, (session, t) in enumerate((("ses-preop", 1), ("ses-postop", 2))):
            record = case["text"][code][visit]
            twin = twin_sessions[session][spec["twin"]]
            osf = osf_row.get(f"{spec['osf']}_t{t}") if osf_row and spec["osf"] else None
            rows.append(
                {
                    "measure": code,
                    "session": session,
                    "openneuro": record,
                    "twin": twin,
                    "twin_agreement": precision_agreement(record, twin),
                    "osf": osf,
                    "osf_agreement": None if osf is None else precision_agreement(osf, record),
                }
            )
    return rows


def percent_improvement(before: float, after: float, sense: int) -> float:
    """Signed so that a positive value is better in the measure's own direction."""
    if before == 0:
        raise ValueError("A percentage of zero is undefined.")
    return 100 * sense * (after - before) / abs(before)


def change_summary(table: list[dict], threshold: float = 1.96) -> list[dict]:
    """Per defined measure: percentage and indices oriented so that positive is better.

    The verdict names a reliable change only when all three indices exceed the threshold
    in the same direction, and otherwise counts the indices beyond it. The largest index
    is reported with the share of bootstrap resamples in which it exceeded the threshold.
    """
    rows = []
    for row in table:
        if not row["defined"]:
            continue
        sense = row["sense"]
        oriented = {name: sense * row[name] for name in INDICES}
        largest = max(oriented, key=lambda name: abs(oriented[name]))
        better = sum(v > threshold for v in oriented.values())
        worse = sum(v < -threshold for v in oriented.values())
        if better == len(INDICES):
            verdict = "reliable improvement on all three indices"
        elif worse == len(INDICES):
            verdict = "reliable decline on all three indices"
        elif better or worse:
            verdict = f"beyond ±{threshold} on {better + worse} of {len(INDICES)} indices only"
        else:
            verdict = "within the controls' retest variation on all three indices"
        rows.append(
            {
                "measure": row["measure"],
                "baseline": row["baseline"],
                "follow_up": row["follow_up"],
                "percent": percent_improvement(row["baseline"], row["follow_up"], sense),
                "oriented": oriented,
                "largest": largest,
                "share_beyond": row["bootstrap"]["share_beyond_threshold"][largest],
                "verdict": verdict,
                "n_reference": row["reference"]["n"],
            }
        )
    return rows


def audit_reported(reported: dict[str, dict], case: dict) -> list[dict]:
    """Compare transcribed reported values with the source, measure by measure."""
    rows = []
    for code, values in reported.items():
        spec = MEASURES[code]
        low, high = spec["bounds"]
        source = case["scores"][code]
        inside = all(low <= v and (high is None or v <= high) for v in values["values"])
        rows.append(
            {
                "measure": code,
                "reported": values["values"],
                "source": source,
                "within_scale": inside,
                "reported_percent": values.get("percent"),
                "percent_from_reported_values": percent_improvement(
                    *values["values"], spec["sense"]
                ),
                "percent_from_source": percent_improvement(*source, spec["sense"]),
            }
        )
    return rows
