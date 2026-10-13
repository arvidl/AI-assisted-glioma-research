"""Denominator of one CGGA clinical table, before any survival curve.

The file is the 6 May 2020 clinical table released with the mRNAseq_693
dataset. Raw sequencing is not read. Age, sex, and sample identifiers are not
returned. No survival model is fit.
"""

import csv
import math
import os
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

_IDH_KNOWN = frozenset({"Wildtype", "Mutant"})
_PRS_KNOWN = frozenset({"Primary", "Recurrent"})


def cgga_clinical_path() -> Path | None:
    """Return the local mRNAseq_693 clinical table when it is present."""
    override = os.environ.get("CGGA_CLINICAL_TABLE")
    candidates = []
    if override:
        candidates.append(Path(override))
    root = Path(__file__).resolve().parents[2] / "data" / "raw" / "cgga"
    candidates.append(root / "CGGA.mRNAseq_693_clinical.20200506.txt.zip")
    candidates.append(root / "CGGA.mRNAseq_693_clinical.20200506.txt")
    for path in candidates:
        if path.is_file():
            return path
    return None


def _rows(path: Path) -> list[dict[str, str]]:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [
                name
                for name in archive.namelist()
                if name.endswith(".txt") and not name.startswith("__MACOSX")
            ]
            if len(names) != 1:
                raise ValueError("The CGGA clinical zip does not contain one text table.")
            with archive.open(names[0]) as handle:
                text = handle.read().decode("utf-8")
    else:
        text = path.read_text(encoding="utf-8")
    table = list(csv.DictReader(text.splitlines(), delimiter="\t"))
    if not table:
        raise ValueError("The CGGA clinical table has no rows.")
    required = {
        "PRS_type",
        "Grade",
        "OS",
        "Censor (alive=0; dead=1)",
        "IDH_mutation_status",
    }
    missing = required - set(table[0])
    if missing:
        raise ValueError(f"The CGGA clinical table is missing columns: {sorted(missing)}.")
    return table


def _blank(value: str) -> bool:
    return value.strip() in {"", "NA"}


def _usable_survival(row: dict[str, str]) -> bool:
    os_text = row["OS"].strip()
    censor = row["Censor (alive=0; dead=1)"].strip()
    if _blank(os_text) or censor not in {"0", "1"}:
        return False
    try:
        days_or_unspecified = float(os_text)
    except ValueError:
        return False
    return days_or_unspecified >= 0 and math.isfinite(days_or_unspecified)


def summarize_cgga_clinical(path: Path | None = None) -> dict | None:
    """Count rows with known IDH status and a usable survival field.

    The OS column is used only as a numeric field. Its unit is not stated in
    the header, so this summary does not name a time unit and does not fit a
    curve. Age and sample identifiers are not copied into the result.
    """
    source = path if path is not None else cgga_clinical_path()
    if source is None:
        return None
    rows = _rows(source)
    grades = sorted({row["Grade"].strip() for row in rows})
    prs_counts = {label: 0 for label in ("Primary", "Recurrent", "other")}
    idh_known = 0
    survival_usable = 0
    both = 0
    both_primary = 0
    both_recurrent = 0
    for row in rows:
        prs = row["PRS_type"].strip()
        prs_counts[prs if prs in _PRS_KNOWN else "other"] += 1
        idh = row["IDH_mutation_status"].strip()
        known = idh in _IDH_KNOWN
        usable = _usable_survival(row)
        idh_known += int(known)
        survival_usable += int(usable)
        if known and usable:
            both += 1
            both_primary += int(prs == "Primary")
            both_recurrent += int(prs == "Recurrent")
    if prs_counts["Primary"] + prs_counts["Recurrent"] + prs_counts["other"] != len(rows):
        raise ValueError("Primary and recurrent counts do not cover the table.")
    return {
        "source_file": source.name,
        "release_date": "2020-05-06",
        "dataset_id": "mRNAseq_693",
        "n_rows": len(rows),
        "n_primary": prs_counts["Primary"],
        "n_recurrent": prs_counts["Recurrent"],
        "n_other_prs": prs_counts["other"],
        "grade_labels": grades,
        "n_idh_known": idh_known,
        "n_survival_usable": survival_usable,
        "n_idh_and_survival": both,
        "n_idh_and_survival_primary": both_primary,
        "n_idh_and_survival_recurrent": both_recurrent,
        "survival_curve": "not_estimated",
        "raw_sequencing": "not_read",
        "ages_exported": False,
    }


def cgga_groups(summary: dict) -> dict[str, int]:
    """Split the table into the four IDH-by-survival cells."""
    rows = int(summary["n_rows"])
    idh = int(summary["n_idh_known"])
    survival = int(summary["n_survival_usable"])
    both = int(summary["n_idh_and_survival"])
    primary = int(summary["n_idh_and_survival_primary"])
    recurrent = int(summary["n_idh_and_survival_recurrent"])
    idh_only = idh - both
    survival_only = survival - both
    neither = rows - both - idh_only - survival_only
    cells = {
        "both": both,
        "idh_only": idh_only,
        "survival_only": survival_only,
        "neither": neither,
        "both_primary": primary,
        "both_recurrent": recurrent,
    }
    if min(cells.values()) < 0 or both != primary + recurrent:
        raise ValueError("The CGGA counts do not form a partition.")
    if idh_only + survival_only + neither + both != rows:
        raise ValueError("The CGGA groups do not cover the table.")
    return cells


def write_cgga_figure(summary: dict, png_path: Path, pdf_path: Path) -> None:
    """Draw the denominator groups. This is not a survival curve."""
    groups = cgga_groups(summary)
    style = {"font.size": 9, "axes.spines.top": False, "axes.spines.right": False}
    left_labels = (
        "Neither",
        "Survival only",
        "IDH only",
        "Both",
    )
    left_values = (
        groups["neither"],
        groups["survival_only"],
        groups["idh_only"],
        groups["both"],
    )
    left_colors = ("#999999", "#009E73", "#E69F00", "#0072B2")
    with plt.rc_context(style):
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), layout="constrained")
        axes[0].barh(left_labels, left_values, color=left_colors)
        axes[0].set_xlim(0, max(left_values) * 1.18)
        axes[0].set_xlabel("Rows")
        axes[0].set_title("IDH status and the survival field")
        for bar, value in zip(axes[0].patches, left_values, strict=True):
            axes[0].text(
                bar.get_width(),
                bar.get_y() + bar.get_height() / 2,
                str(value),
                ha="left",
                va="center",
                fontsize=8,
            )
        right_labels = ("Recurrent", "Primary")
        right_values = (groups["both_recurrent"], groups["both_primary"])
        axes[1].barh(right_labels, right_values, color=("#CC79A7", "#0072B2"))
        axes[1].set_xlim(0, max(right_values) * 1.18)
        axes[1].set_xlabel("Rows with both fields")
        axes[1].set_title("Primary and recurrent disease")
        for bar, value in zip(axes[1].patches, right_values, strict=True):
            axes[1].text(
                bar.get_width(),
                bar.get_y() + bar.get_height() / 2,
                str(value),
                ha="left",
                va="center",
                fontsize=8,
            )
        png_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_path, dpi=180)
        fig.savefig(pdf_path, metadata={"CreationDate": None, "ModDate": None})
        plt.close(fig)
