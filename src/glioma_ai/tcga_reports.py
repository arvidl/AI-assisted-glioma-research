"""What a brain-tumor pathology report states, and what it does not.

Reports are the machine-readable TCGA corpus of Kefeli and Tatonetti. Only
cases listed locally as TCGA-GBM or TCGA-LGG are read. The extractor records
whether a histologic term, IDH, or MGMT is present. It does not assign a
genotype when the word is absent, and it does not return report text.
"""

import csv
import io
import os
import re
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

_CASE_ID = re.compile(r"^(TCGA-[A-Z0-9]{2}-[A-Z0-9]{4})")
_HISTOLOGY = (
    "glioblastoma",
    "oligoastrocytoma",
    "oligodendroglioma",
    "astrocytoma",
    "glioma",
)
_IDH = re.compile(r"\bidh(?:\s*[-]?\s*[12])?\b", re.IGNORECASE)
_MGMT = re.compile(r"\bmgmt\b", re.IGNORECASE)


def tcga_reports_paths() -> tuple[Path, Path] | None:
    """Return the report archive and the GDC case list when both are present."""
    override = os.environ.get("TCGA_REPORTS_ROOT")
    root = (
        Path(override)
        if override
        else Path(__file__).resolve().parents[2] / "data" / "raw" / "tcga-reports"
    )
    archive = root / "TCGA_Reports.csv.zip"
    cases = root / "gdc_tcga_gbm_lgg_submitter_ids.tsv"
    if archive.is_file() and cases.is_file():
        return archive, cases
    return None


def report_statements(text: str) -> dict[str, str]:
    """Record stated histology terms and whether IDH or MGMT words occur.

    IDH and MGMT are ``stated`` or ``not_stated``. A genotype is not inferred.
    """
    if not isinstance(text, str):
        raise ValueError("A pathology report must be text.")
    found = [term for term in _HISTOLOGY if re.search(rf"\b{term}\b", text, re.IGNORECASE)]
    return {
        "histology": "stated" if found else "not_stated",
        "idh": "stated" if _IDH.search(text) else "not_stated",
        "mgmt": "stated" if _MGMT.search(text) else "not_stated",
    }


def _brain_cases(path: Path) -> dict[str, str]:
    cases = {}
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None or {"submitter_id", "project_id"} - set(reader.fieldnames):
            raise ValueError("The GDC case list needs submitter_id and project_id columns.")
        for row in reader:
            project = row["project_id"].strip()
            if project not in {"TCGA-GBM", "TCGA-LGG"}:
                raise ValueError(f"Unexpected project in the brain-tumor case list: {project}.")
            cases[row["submitter_id"].strip()] = project
    if not cases:
        raise ValueError("The GDC brain-tumor case list is empty.")
    return cases


def summarize_tcga_reports(
    archive: Path | None = None,
    case_list: Path | None = None,
) -> dict | None:
    """Count GBM and LGG reports that state histology without IDH or MGMT."""
    if archive is None or case_list is None:
        found = tcga_reports_paths()
        if found is None:
            return None
        archive, case_list = found
    cases = _brain_cases(case_list)
    n_gdc_gbm = sum(project == "TCGA-GBM" for project in cases.values())
    n_gdc_lgg = sum(project == "TCGA-LGG" for project in cases.values())
    counts = {
        "n_reports": 0,
        "n_gbm_reports": 0,
        "n_lgg_reports": 0,
        "n_histology_stated": 0,
        "n_idh_stated": 0,
        "n_mgmt_stated": 0,
        "n_archive_rows": 0,
        "n_histology_without_idh_or_mgmt": 0,
    }
    seen_cases: set[str] = set()
    with zipfile.ZipFile(archive) as bundle:
        names = [
            name
            for name in bundle.namelist()
            if name.endswith(".csv") and not name.startswith("__")
        ]
        if names != ["TCGA_Reports.csv"]:
            raise ValueError("The report archive does not contain TCGA_Reports.csv.")
        with bundle.open("TCGA_Reports.csv") as handle:
            reader = csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8", newline=""))
            if reader.fieldnames != ["patient_filename", "text"]:
                raise ValueError("The report table does not have the expected columns.")
            for row in reader:
                counts["n_archive_rows"] += 1
                match = _CASE_ID.match(row["patient_filename"])
                if match is None:
                    continue
                project = cases.get(match.group(1))
                if project is None:
                    continue
                fields = report_statements(row["text"])
                if fields["idh"] not in {"stated", "not_stated"} or fields["mgmt"] not in {
                    "stated",
                    "not_stated",
                }:
                    raise ValueError("IDH and MGMT must remain presence flags.")
                counts["n_reports"] += 1
                counts["n_gbm_reports"] += int(project == "TCGA-GBM")
                counts["n_lgg_reports"] += int(project == "TCGA-LGG")
                seen_cases.add(match.group(1))
                histology = fields["histology"] == "stated"
                idh = fields["idh"] == "stated"
                mgmt = fields["mgmt"] == "stated"
                counts["n_histology_stated"] += int(histology)
                counts["n_idh_stated"] += int(idh)
                counts["n_mgmt_stated"] += int(mgmt)
                counts["n_histology_without_idh_or_mgmt"] += int(histology and not idh and not mgmt)
    if counts["n_reports"] == 0:
        raise ValueError("No TCGA-GBM or TCGA-LGG reports were found in the local archive.")
    counts["n_cases"] = len(seen_cases)
    counts["n_gdc_cases"] = len(cases)
    counts["n_gdc_gbm"] = n_gdc_gbm
    counts["n_gdc_lgg"] = n_gdc_lgg
    counts["source_archive"] = archive.name
    counts["case_list"] = case_list.name
    counts["projects"] = ["TCGA-GBM", "TCGA-LGG"]
    counts["report_text_exported"] = False
    counts["genotype_inferred"] = False
    return counts


def tcga_groups(summary: dict) -> dict[str, int]:
    """Split the archive and the matched reports into the reported sets."""
    reports = int(summary["n_reports"])
    histology = int(summary["n_histology_stated"])
    neither = int(summary["n_histology_without_idh_or_mgmt"])
    cells = {
        "archive_rows": int(summary["n_archive_rows"]),
        "gdc_cases": int(summary["n_gdc_cases"]),
        "matched_reports": reports,
        "gbm_reports": int(summary["n_gbm_reports"]),
        "lgg_reports": int(summary["n_lgg_reports"]),
        "histology_stated": histology,
        "histology_absent": reports - histology,
        "histology_with_marker": histology - neither,
        "histology_without_markers": neither,
        "idh_stated": int(summary["n_idh_stated"]),
        "mgmt_stated": int(summary["n_mgmt_stated"]),
        "archive_unmatched": int(summary["n_archive_rows"]) - reports,
        "gdc_without_report": int(summary["n_gdc_cases"]) - reports,
    }
    if min(cells.values()) < 0:
        raise ValueError("The report counts do not form a partition.")
    if cells["gbm_reports"] + cells["lgg_reports"] != reports:
        raise ValueError("GBM and LGG reports do not cover the matched set.")
    covered = cells["histology_absent"] + cells["histology_with_marker"]
    covered += cells["histology_without_markers"]
    if covered != reports:
        raise ValueError("The histology groups do not cover the matched reports.")
    return cells


def write_tcga_figure(summary: dict, png_path: Path, pdf_path: Path) -> None:
    """Draw the matched-report groups. IDH and MGMT bars may overlap."""
    groups = tcga_groups(summary)
    style = {"font.size": 9, "axes.spines.top": False, "axes.spines.right": False}
    left_labels = (
        "No listed histologic term",
        "Histology and IDH or MGMT",
        "Histology, neither marker",
    )
    left_values = (
        groups["histology_absent"],
        groups["histology_with_marker"],
        groups["histology_without_markers"],
    )
    with plt.rc_context(style):
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3), layout="constrained")
        axes[0].barh(left_labels, left_values, color=("#999999", "#0072B2", "#D55E00"))
        axes[0].set_xlim(0, max(left_values) * 1.22)
        axes[0].set_xlabel("Matched reports")
        axes[0].set_title("Histologic term and marker abbreviations")
        for bar, value in zip(axes[0].patches, left_values, strict=True):
            axes[0].text(
                bar.get_width(),
                bar.get_y() + bar.get_height() / 2,
                str(value),
                ha="left",
                va="center",
                fontsize=8,
            )
        right_labels = ("MGMT stated", "IDH stated")
        right_values = (groups["mgmt_stated"], groups["idh_stated"])
        axes[1].barh(right_labels, right_values, color=("#E69F00", "#0072B2"))
        axes[1].set_xlim(0, max(right_values) * 1.22)
        axes[1].set_xlabel("Matched reports")
        axes[1].set_title("Separate abbreviation counts")
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
