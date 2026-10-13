"""Generate local empirical figures only after source and case checks."""

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from glioma_ai.cantab import (
    DOMAINS,
    METRICS,
    cohort_summary,
    read_release,
    release_reference,
    verified_case,
    verify_release,
)
from glioma_ai.provenance import environment_record, sha256


def write_cantab_example(
    release_dir: Path,
    output: Path,
    case_config: Path | None = None,
    paper_dir: Path | None = None,
) -> dict:
    rows = read_release(release_dir)
    summary = cohort_summary(rows)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    case = None
    if case_config is not None:
        config = json.loads(Path(case_config).read_text())
        sessions = Path(config["sessions_path"])
        if not sessions.is_absolute():
            sessions = Path(case_config).resolve().parent / sessions
        case = verified_case(rows, sessions, config["source_case_id"])
        figure, axes = plt.subplots(1, 4, figsize=(11.8, 3.15), layout="constrained")
        names = ["RTI five-choice", "RVP sensitivity", "SOC minimum moves", "SSP spatial span"]
        for axis, key, name in zip(axes, DOMAINS, names, strict=True):
            spec, score = METRICS[key], case["scores"][key]
            values = [score["before"], score["followup"]]
            axis.plot([0, 1], values, color="#90a4a6", linewidth=1.5, zorder=1)
            axis.scatter([0, 1], values, color=["#173e43", "#31858f"], s=65, zorder=2)
            for x, y, label in zip([0, 1], values, score["released_text"], strict=True):
                axis.annotate(
                    label,
                    (x, y),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=11,
                )
            axis.set_xticks([0, 1], ["Preoperative", "Follow-up"], fontsize=9)
            axis.set_xlim(-0.28, 1.28)
            axis.set_title(f"{spec['name']}\n{name}", fontsize=11)
            axis.set_ylabel(spec["unit"], fontsize=11)
            if key == "RVP_A":
                axis.set_ylim(0, 1.05)
            elif spec["unit"] in {"problems", "span"}:
                axis.yaxis.set_major_locator(MaxNLocator(integer=True))
                axis.set_ylim(max(0, min(values) - 1.5), max(values) + 2)
            else:
                pad = max(25, (max(values) - min(values)) * 0.5)
                axis.set_ylim(max(0, min(values) - pad), max(values) + 1.5 * pad)
            axis.spines[["top", "right"]].set_visible(False)
        for suffix in ("pdf", "png"):
            figure.savefig(output / f"cantab_case.{suffix}", dpi=200)
        plt.close(figure)
        (output / "cantab_case.json").write_text(json.dumps(case, indent=2) + "\n")
    (output / "cantab_cohort.json").write_text(json.dumps(summary, indent=2) + "\n")
    artifacts = ["cantab_cohort.json"] + (
        ["cantab_case.json", "cantab_case.pdf", "cantab_case.png"] if case else []
    )
    record = {
        **environment_record(),
        "evidence_type": summary["evidence_type"],
        "source_url": release_reference()["project_url"],
        "input_sha256": verify_release(release_dir),
        "output_sha256": {name: sha256(output / name) for name in artifacts},
        "cohort": summary,
        "case_verified": case is not None,
        "ai_role": "research assistance with source audit, implementation and study design",
        "trained_prediction_model_run": False,
        "reliable_change_assessed": False,
        "human_scientific_review": "pending",
    }
    (output / "cantab_run.json").write_text(json.dumps(record, indent=2) + "\n")
    if paper_dir is not None:
        paper_dir = Path(paper_dir)
        paper_dir.mkdir(parents=True, exist_ok=True)
        macros = {"CantabBehavioralN": str(summary["n_rows"])}
        for group, name in (("GLI", "Glioma"), ("MEN", "Meningioma"), ("CON", "Control")):
            group_summary = summary["groups"][group]
            macros[f"Cantab{name}N"] = str(group_summary["baseline_rows"])
            macros[f"Cantab{name}PairedN"] = str(group_summary["complete_four_domains"])
        if case:
            shutil.copy2(output / "cantab_case.pdf", paper_dir / "cantab_case.pdf")
            macros.update(
                CantabCaseInterval=str(case["assessment_interval_days"]),
                CantabVerifiedMetricN=str(case["verified_metric_count"]),
                CantabLocalMetricN=str(case["local_cantab_metric_count"]),
                CantabExactCells=str(sum(a["agreement"] == "exact" for a in case["audit"])),
                CantabPrecisionCells=str(
                    sum(a["agreement"] == "at_release_precision" for a in case["audit"])
                ),
            )
        else:
            (paper_dir / "cantab_case.pdf").unlink(missing_ok=True)
        (paper_dir / "cantab_numbers.tex").write_text(
            "% Generated from the pinned OSF behavioral release; keep local.\n"
            + "".join(f"\\newcommand{{\\{key}}}{{{value}}}\n" for key, value in macros.items())
        )
    return {
        "cohort": summary,
        "case_verified": case is not None,
        "case_audit": case["audit"] if case else None,
        "prediction_performed": False,
        "reliable_change_assessed": False,
    }
