"""The clinical table and the pathology reports stay aggregate and uninferred."""

import csv
import zipfile

from glioma_ai.cgga_clinical import cgga_groups, summarize_cgga_clinical, write_cgga_figure
from glioma_ai.tcga_reports import (
    report_statements,
    summarize_tcga_reports,
    tcga_groups,
    write_tcga_figure,
)


def test_report_statements_do_not_invent_idh_or_mgmt():
    bare = report_statements("Diagnosis: glioblastoma. No further molecular studies.")
    stated = report_statements("Glioblastoma, IDH1 R132H mutant, MGMT promoter methylated.")
    assert bare == {"histology": "stated", "idh": "not_stated", "mgmt": "not_stated"}
    assert stated["idh"] == "stated"
    assert stated["mgmt"] == "stated"
    assert "mutant" not in stated.values()


def test_cgga_summary_counts_the_denominator_without_ages(tmp_path):
    path = tmp_path / "clinical.txt"
    header = [
        "CGGA_ID",
        "PRS_type",
        "Histology",
        "Grade",
        "Gender",
        "Age",
        "OS",
        "Censor (alive=0; dead=1)",
        "IDH_mutation_status",
    ]
    rows = [
        ["A", "Primary", "GBM", "WHO IV", "Female", "43", "100", "1", "Wildtype"],
        ["B", "Recurrent", "rGBM", "WHO IV", "Male", "50", "NA", "NA", "Mutant"],
        ["C", "Primary", "A", "WHO II", "Male", "30", "20", "0", "NA"],
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)
    summary = summarize_cgga_clinical(path)
    assert summary["n_rows"] == 3
    assert summary["n_primary"] == 2
    assert summary["n_recurrent"] == 1
    assert summary["n_idh_and_survival"] == 1
    assert summary["ages_exported"] is False
    assert "Age" not in summary
    assert "CGGA_ID" not in summary
    groups = cgga_groups(summary)
    assert groups == {
        "both": 1,
        "idh_only": 1,
        "survival_only": 1,
        "neither": 0,
        "both_primary": 1,
        "both_recurrent": 0,
    }
    figure = tmp_path / "cgga.pdf"
    write_cgga_figure(summary, tmp_path / "cgga.png", figure)
    assert figure.stat().st_size > 0


def test_tcga_summary_counts_reports_that_omit_the_markers(tmp_path):
    cases = tmp_path / "cases.tsv"
    cases.write_text("submitter_id\tproject_id\nTCGA-02-0001\tTCGA-GBM\nTCGA-DU-0002\tTCGA-LGG\n")
    archive = tmp_path / "TCGA_Reports.csv.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        with bundle.open("TCGA_Reports.csv", "w") as handle:
            handle.write(
                b"patient_filename,text\n"
                b"TCGA-02-0001.aaaa,Glioblastoma.\n"
                b'TCGA-DU-0002.bbbb,"Astrocytoma, IDH1 mutant."\n'
                b"TCGA-AA-0003.cccc,Not a listed brain project.\n"
            )
    summary = summarize_tcga_reports(archive, cases)
    assert summary["n_reports"] == 2
    assert summary["n_gbm_reports"] == 1
    assert summary["n_lgg_reports"] == 1
    assert summary["n_archive_rows"] == 3
    assert summary["n_gdc_cases"] == 2
    assert summary["n_gdc_gbm"] == 1
    assert summary["n_gdc_lgg"] == 1
    assert summary["n_histology_without_idh_or_mgmt"] == 1
    assert summary["report_text_exported"] is False
    assert summary["genotype_inferred"] is False
    groups = tcga_groups(summary)
    assert groups["histology_without_markers"] == 1
    assert groups["histology_with_marker"] == 1
    assert groups["archive_unmatched"] == 1
    figure = tmp_path / "tcga.pdf"
    write_tcga_figure(summary, tmp_path / "tcga.png", figure)
    assert figure.stat().st_size > 0
